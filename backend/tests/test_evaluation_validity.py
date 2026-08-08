import json
import sys

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import select

from app.controller.policy import ControllerDecision
from app.evaluation import cli
from app.evaluation.ablations import condition_config
from app.evaluation.cli import validate_workload
from app.evaluation.config import ExperimentConfig
from app.evaluation.learning_effects import (
    apply_misconception_remediation,
    apply_recommendation_learning,
)
from app.evaluation.metrics import condition_metrics, learner_metrics
from app.evaluation.ml_metrics import synthetic_ml_metrics
from app.evaluation.policy import EvaluationPolicy
from app.evaluation.simulator import run_experiment
from app.evaluation.statistics import (
    bootstrap_confidence_interval,
    cohens_d,
    paired_bootstrap_difference,
)
from app.evaluation.suite import run_suite
from app.models.question import Question
from app.offline.content_availability import OfflineAvailability
from app.schemas.interactions import InteractionCreate
from app.services.interaction_service import process_interaction


def _direct_interaction(client, policy: EvaluationPolicy):
    learner = client(
        "POST", "/learners", json={"name": "Policy", "age_group": "10-12", "grade": 5}
    ).json()
    with client.session_factory() as db:
        question = db.scalar(select(Question).where(Question.id == "whole_numbers_01"))
        return process_interaction(
            InteractionCreate(
                learner_id=learner["id"],
                question_id=question.id,
                submitted_answer=question.correct_answer,
                response_time_ms=1000,
            ),
            question,
            db,
            policy,
        )


def test_disabled_bkt_skips_updater(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.interaction_service.update_mastery",
        lambda *args: pytest.fail("BKT updater was called"),
    )
    result = _direct_interaction(client, EvaluationPolicy(enable_bkt=False))
    assert result.learner_state.mastery_probability == 1.0


def test_disabled_misconceptions_skips_detector(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.interaction_service.detect_misconceptions",
        lambda *args: pytest.fail("misconception detector was called"),
    )
    result = _direct_interaction(client, EvaluationPolicy(enable_misconceptions=False))
    assert not result.misconception.detected
    assert result.recommendation.adaptation_path != "misconception_remediation"


def test_disabled_ml_never_checks_or_calls_predictor(client, monkeypatch) -> None:
    class DisabledRegistry:
        def is_available(self):
            pytest.fail("ML availability was checked")

    monkeypatch.setattr(
        "app.services.interaction_service.get_response_predictor_registry",
        lambda: DisabledRegistry(),
    )
    result = _direct_interaction(client, EvaluationPolicy(enable_ml=False))
    assert result.recommendation.adaptation_path != "lightweight_ml_recommendation"
    assert result.recommendation.selected_candidate_predicted_probability is None


@pytest.mark.parametrize(
    ("policy", "assertion"),
    [
        (EvaluationPolicy(enable_uncertainty=False), lambda value: value.uncertainty == 0.0),
        (
            EvaluationPolicy(enable_forgetting=False),
            lambda value: value.retained_mastery == 0.69,
        ),
        (
            EvaluationPolicy(enable_resource_awareness=False),
            lambda value: value.resource.level == "high",
        ),
    ],
)
def test_policy_neutralizes_controller_signal(client, monkeypatch, policy, assertion) -> None:
    captured = None

    def capture(value):
        nonlocal captured
        captured = value
        return ControllerDecision(
            adaptation_path="bkt_based_recommendation",
            reason="capture",
            triggered_rules=["capture"],
            rejected_paths=[],
            estimated_computational_cost_ms=3.0,
            decision_confidence=1.0,
            resource_score=value.resource.score,
        )

    monkeypatch.setattr("app.services.interaction_service.decide_adaptation", capture)
    result = _direct_interaction(client, policy)
    assert captured is not None
    if not policy.enable_forgetting:
        assert captured.retained_mastery == result.learner_state.mastery_probability
    else:
        assert assertion(captured)


def test_disabled_offline_adaptation_never_exposes_cache(client, monkeypatch) -> None:
    captured = None

    monkeypatch.setattr(
        "app.services.interaction_service.resolve_offline_availability",
        lambda *args: OfflineAvailability(
            True,
            ["whole_numbers_practice"],
            "available",
            True,
            "cached_offline_recommendation",
            None,
        ),
    )

    def capture(value):
        nonlocal captured
        captured = value
        return ControllerDecision(
            adaptation_path="bkt_based_recommendation",
            reason="capture",
            triggered_rules=["capture"],
            rejected_paths=[],
            estimated_computational_cost_ms=3.0,
            decision_confidence=1.0,
            resource_score=value.resource.score,
        )

    monkeypatch.setattr("app.services.interaction_service.decide_adaptation", capture)
    result = _direct_interaction(client, EvaluationPolicy(enable_offline_adaptation=False))
    assert captured is not None and not captured.offline_cache_available
    assert result.recommendation.adaptation_path != "cached_offline_recommendation"


def test_exact_bkt_and_static_policy_matrices() -> None:
    base = ExperimentConfig(learner_profile_distribution={"mixed": 1.0})
    bkt = condition_config(base, "bkt_only")
    assert (
        bkt.enable_adaptation,
        bkt.enable_bkt,
        bkt.enable_uncertainty,
        bkt.enable_forgetting,
        bkt.enable_misconceptions,
        bkt.enable_resource_awareness,
        bkt.enable_offline_adaptation,
        bkt.enable_ml,
    ) == (True, True, False, False, False, False, False, False)
    static = condition_config(base, "static_baseline")
    assert not any(
        (
            static.enable_adaptation,
            static.enable_bkt,
            static.enable_uncertainty,
            static.enable_forgetting,
            static.enable_misconceptions,
            static.enable_resource_awareness,
            static.enable_offline_adaptation,
            static.enable_ml,
        )
    )


def test_static_baseline_sequence_is_profile_independent(tmp_path) -> None:
    sequences = []
    for profile in ("strong", "struggling"):
        config = condition_config(
            ExperimentConfig(
                experiment_name=profile,
                learner_count=1,
                interactions_per_learner=3,
                output_dir=str(tmp_path / "artifacts"),
                learner_profile_distribution={profile: 1.0},
            ),
            "static_baseline",
        )
        interactions = pd.read_parquet(run_experiment(config) / "interactions.parquet")
        sequences.append(interactions[["question_id", "selected_activity_id"]].values.tolist())
    assert sequences[0] == sequences[1]


def test_cross_concept_effect_updates_only_selected_concept() -> None:
    latent = {"target": 0.4, "prerequisite": 0.2}
    before, after = apply_recommendation_learning(
        latent,
        "target",
        "prerequisite",
        1.0,
        np.random.default_rng(7),
    )
    assert before == 0.2 and after > before
    assert latent["target"] == 0.4
    assert latent["prerequisite"] == after


def test_matching_remediation_reduces_synthetic_misconception() -> None:
    assert apply_misconception_remediation(0.6, True) == 0.3
    assert apply_misconception_remediation(0.6, False) == 0.6


def _metric_frames():
    interactions = pd.DataFrame(
        [
            {
                "synthetic_learner_id": "a",
                "step": 0,
                "system_mean_mastery_after": 0.5,
                "response_time_ms": 100,
                "resource_score": 0.8,
                "offline": False,
                "fallback_used": False,
                "actual_adaptation_path": "bkt_based_recommendation",
                "measured_total_adaptive_latency_ms": 2.0,
                "estimated_computational_cost_ms": 3.0,
                "misconception_id": None,
                "synthetic_misconception_before": 0.0,
                "synthetic_misconception_after": 0.0,
                "synthetic_misconception_resolved": False,
                "event_code": "recommendation_success",
                "matching_offline_activity_ids": "[]",
            },
            {
                "synthetic_learner_id": "a",
                "step": 1,
                "system_mean_mastery_after": 0.85,
                "response_time_ms": 200,
                "resource_score": 0.6,
                "offline": False,
                "fallback_used": True,
                "actual_adaptation_path": "bkt_based_recommendation",
                "measured_total_adaptive_latency_ms": 4.0,
                "estimated_computational_cost_ms": 5.0,
                "misconception_id": "m",
                "synthetic_misconception_before": 0.3,
                "synthetic_misconception_after": 0.1,
                "synthetic_misconception_resolved": True,
                "event_code": "fallback",
                "matching_offline_activity_ids": "[]",
            },
        ]
    )
    concepts = pd.DataFrame(
        [
            {
                "synthetic_learner_id": "a",
                "initial_system_mastery": 0.2,
                "final_system_mastery": 0.8,
                "initial_synthetic_mastery": 0.3,
                "final_synthetic_mastery": 0.6,
            },
            {
                "synthetic_learner_id": "a",
                "initial_system_mastery": 0.4,
                "final_system_mastery": 0.9,
                "initial_synthetic_mastery": 0.5,
                "final_synthetic_mastery": 0.7,
            },
        ]
    )
    return interactions, concepts


def test_true_multiconcept_initial_gain_threshold_and_cost_metrics() -> None:
    interactions, concepts = _metric_frames()
    learner = learner_metrics(interactions, concepts, 0.8).iloc[0]
    assert learner.initial_mean_mastery == pytest.approx(0.3)
    assert learner.final_mean_mastery == pytest.approx(0.85)
    assert learner.mastery_gain == pytest.approx(0.55)
    assert learner.interactions_to_mastery_threshold == 2
    assert learner.estimated_total_compute_cost_ms == 8.0
    summary = condition_metrics(interactions, concepts, 0.8)
    assert summary["misconception_resolution_rate"] == 1.0
    assert summary["fallback_rate"] == 0.5


def test_synthetic_ml_metrics_are_temporally_aligned_and_exact() -> None:
    frame = pd.DataFrame(
        [
            {
                "synthetic_learner_id": "a",
                "step": 0,
                "concept_id": "x",
                "selected_concept_id": "y",
                "selected_candidate_predicted_probability": 0.8,
                "correct": False,
            },
            {
                "synthetic_learner_id": "a",
                "step": 1,
                "concept_id": "y",
                "selected_concept_id": "x",
                "selected_candidate_predicted_probability": 0.2,
                "correct": True,
            },
            {
                "synthetic_learner_id": "a",
                "step": 2,
                "concept_id": "x",
                "selected_concept_id": "x",
                "selected_candidate_predicted_probability": None,
                "correct": False,
            },
        ]
    )
    metrics = synthetic_ml_metrics(frame)
    assert metrics["synthetic_ml_matched_samples"] == 2
    assert metrics["synthetic_brier_score"] == pytest.approx(0.04)
    assert metrics["synthetic_roc_auc"] == 1.0


def test_seeded_bootstrap_paired_difference_and_effect_size() -> None:
    assert bootstrap_confidence_interval([1, 2, 3], 7, 100) == bootstrap_confidence_interval(
        [1, 2, 3], 7, 100
    )
    difference, low, high = paired_bootstrap_difference([3, 4], [1, 2], 4, 100)
    assert difference == 2.0
    assert low == high == 2.0
    assert cohens_d([3, 4], [1, 2]) == 0.0


def test_large_run_guard() -> None:
    config = ExperimentConfig(
        learner_count=100,
        interactions_per_learner=100,
        max_interactions_without_override=100,
        learner_profile_distribution={"mixed": 1.0},
    )
    with pytest.raises(SystemExit, match="Refusing"):
        validate_workload(config, 2, 2, False)
    validate_workload(config, 2, 2, True)


def test_cli_run_summarize_and_suite_commands(tmp_path, monkeypatch, capsys) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        ExperimentConfig(
            learner_profile_distribution={"mixed": 1.0},
            output_dir=str(tmp_path / "artifacts"),
        ).model_dump_json()
    )
    run_path = tmp_path / "run"
    run_path.mkdir()
    (run_path / "summary.json").write_text('{"simulated_results": true}')
    monkeypatch.setattr(cli, "run_experiment", lambda config: run_path)
    monkeypatch.setattr(sys, "argv", ["evaluation", "run", "--config", str(config_path)])
    cli.main()
    assert str(run_path) in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["evaluation", "summarize", "--experiment", str(run_path)])
    cli.main()
    assert "simulated_results" in capsys.readouterr().out
    suite_path = tmp_path / "suite"
    monkeypatch.setattr(cli, "run_suite", lambda *args: suite_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["evaluation", "run-ablation-suite", "--config", str(config_path), "--seeds", "1"],
    )
    cli.main()
    assert str(suite_path) in capsys.readouterr().out


def test_multi_seed_suite_writes_aggregate_statistics_plots_and_tables(tmp_path) -> None:
    config = ExperimentConfig(
        experiment_name="suite-test",
        random_seed=3,
        learner_count=1,
        interactions_per_learner=2,
        output_dir=str(tmp_path / "artifacts"),
        learner_profile_distribution={"mixed": 1.0},
    )
    directory = run_suite(config, ("full", "no_ml"), [3])
    for filename in (
        "suite_summary.json",
        "seed_metrics.csv",
        "aggregate_metrics.csv",
        "paired_comparisons.csv",
    ):
        assert (directory / filename).exists()
    assert (directory / "plots" / "mean_final_mastery.png").exists()
    assert (directory / "tables" / "main_comparison.tex").exists()
    summary = json.loads((directory / "suite_summary.json").read_text())
    assert summary["simulated_results"] is True
    assert summary["educational_effectiveness_validated"] is False
