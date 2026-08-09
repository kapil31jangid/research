import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.core.config import Settings
from app.evaluation.ablations import ABLATIONS, condition_config
from app.evaluation.config import ExperimentConfig
from app.evaluation.publication import publish_suite
from app.evaluation.resource_simulator import simulate_resource
from app.evaluation.sensitivity import run_weight_sensitivity
from app.evaluation.simulator import run_experiment
from app.evaluation.synthetic_learners import PROFILES, generate_learners
from app.evaluation.validation import validate_interaction_frame
from app.recommendation.candidate_generator import ActivityCandidate
from app.recommendation.scorer import score_candidate
from app.resources.scoring import calculate_resource_score


def test_final_suite_has_exactly_the_nine_paper_conditions() -> None:
    assert ABLATIONS == (
        "static_baseline",
        "bkt_only",
        "bkt_uncertainty",
        "pedagogical_adaptive",
        "full",
        "no_uncertainty",
        "no_forgetting",
        "no_misconceptions",
        "no_resource_awareness",
    )


def test_bkt_baselines_disable_non_bkt_controller_signals() -> None:
    base = ExperimentConfig(learner_profile_distribution={"mixed": 1.0})
    bkt = condition_config(base, "bkt_only")
    bkt_uncertainty = condition_config(base, "bkt_uncertainty")
    assert not bkt.enable_prerequisites
    assert not bkt.enable_forgetting
    assert not bkt.enable_uncertainty
    assert not bkt_uncertainty.enable_prerequisites
    assert bkt_uncertainty.enable_uncertainty


def test_simulator_latent_mastery_is_not_copied_to_system_state(tmp_path) -> None:
    first_rows = []
    for profile in ("fast_learner", "slow_learner"):
        config = ExperimentConfig(
            experiment_name=f"separation-{profile}",
            learner_count=1,
            interactions_per_learner=1,
            output_dir=str(tmp_path / "artifacts"),
            learner_profile_distribution={profile: 1.0},
            bootstrap_samples=100,
        )
        first_rows.append(pd.read_parquet(run_experiment(config) / "interactions.parquet").iloc[0])
    assert first_rows[0].system_mastery_before == pytest.approx(0.2)
    assert first_rows[1].system_mastery_before == pytest.approx(0.2)
    assert first_rows[0].synthetic_assessed_mastery_before != pytest.approx(0.2)
    assert first_rows[1].synthetic_assessed_mastery_before != pytest.approx(0.2)
    assert (
        first_rows[0].synthetic_assessed_mastery_before
        != first_rows[1].synthetic_assessed_mastery_before
    )


def test_resource_ablation_preserves_external_resource_exposure(tmp_path) -> None:
    rows = []
    base = ExperimentConfig(
        experiment_name="resource-exposure",
        learner_count=1,
        interactions_per_learner=1,
        random_seed=19,
        output_dir=str(tmp_path / "artifacts"),
        learner_profile_distribution={"constrained_resource": 1.0},
        bootstrap_samples=100,
        reuse_completed_runs=False,
    )
    for condition in ("full", "no_resource_awareness"):
        frame = pd.read_parquet(
            run_experiment(condition_config(base, condition)) / "interactions.parquet"
        )
        rows.append(frame.iloc[0])
    assert rows[0].resource_profile == rows[1].resource_profile == "low_end"
    assert rows[0].resource_score == pytest.approx(rows[1].resource_score)
    assert rows[0].network_available == rows[1].network_available


def test_publication_profiles_expose_bounded_parameters() -> None:
    required = {
        "fast_learner",
        "slow_learner",
        "elevated_guess",
        "elevated_slip",
        "stronger_forgetting",
        "misconception_prone",
        "intermittent",
        "constrained_resource",
    }
    assert required <= PROFILES.keys()
    for name in required:
        profile = PROFILES[name]
        for value in (
            profile.initial_mastery,
            profile.learning_rate,
            profile.guess_probability,
            profile.slip_probability,
            profile.hint_probability,
            profile.misconception_tendency,
            profile.forgetting_rate,
            profile.interruption_probability,
            profile.offline_probability,
        ):
            assert 0.0 <= value <= 1.0
    learners = generate_learners(2, ["concept"], 8, {"elevated_guess": 1.0})
    assert all(
        item.guess_probability == PROFILES["elevated_guess"].guess_probability for item in learners
    )


def test_resource_score_equation_and_missing_battery_are_exact() -> None:
    assert calculate_resource_score(100, 100, 0, 100, True, 1.0) == pytest.approx(1.0)
    assert calculate_resource_score(100, 100, 100, 0, False, 0.0) == pytest.approx(0.35)
    assert calculate_resource_score(0, 100, 100, None, False, None) == pytest.approx(0.10)


def test_simulated_resources_never_exceed_physical_bounds() -> None:
    snapshot = simulate_resource("high_end", np.random.default_rng(19))
    assert 0 < snapshot.available_memory_mb <= snapshot.total_memory_mb
    assert 0 <= snapshot.cpu_percent <= 100
    assert snapshot.battery_percent is not None
    assert 0 <= snapshot.battery_percent <= 100


def test_activity_score_equation_uses_configured_weights() -> None:
    candidate = ActivityCandidate(
        "concept",
        "activity",
        expected_learning_gain=0.8,
        prerequisite_relevance=0.7,
        retention_need=0.6,
        information_gain=0.5,
        misconception_relevance=0.4,
        computational_cost=0.3,
    )
    settings = Settings(ml_learning_zone_weight=0.0, activity_cost_reference_ms=1.0)
    expected = 0.30 * 0.8 + 0.20 * 0.7 + 0.20 * 0.6 + 0.15 * 0.5 + 0.10 * 0.4 - 0.05 * 0.3
    assert score_candidate(candidate, 1.0, settings)[0] == pytest.approx(expected)


def test_integrity_validator_rejects_duplicate_learner_steps() -> None:
    frame = pd.DataFrame(
        {
            "condition": ["full", "full"],
            "seed": [1, 1],
            "synthetic_learner_id": ["a", "a"],
            "step": [0, 0],
        }
    )
    config = ExperimentConfig(
        learner_count=1,
        interactions_per_learner=2,
        random_seed=1,
        learner_profile_distribution={"mixed": 1.0},
    )
    with pytest.raises(ValueError, match="missing columns|Duplicate"):
        validate_interaction_frame(frame, config)


def test_validated_suite_is_published_in_paper_layout(tmp_path) -> None:
    suite = tmp_path / "suite"
    for name in ("tables", "plots", "config"):
        (suite / name).mkdir(parents=True)
        (suite / name / "sample.txt").write_text("sample", encoding="utf-8")
    (suite / "suite_summary.json").write_text(
        json.dumps({"integrity_valid": True}), encoding="utf-8"
    )
    (suite / "provenance.json").write_text("{}", encoding="utf-8")
    (suite / "config.json").write_text("{}", encoding="utf-8")
    for filename in (
        "interactions.parquet",
        "interactions.csv",
        "learner_metrics.parquet",
        "learner_metrics.csv",
        "concept_metrics.parquet",
        "concept_metrics.csv",
    ):
        (suite / filename).write_text("fixture", encoding="utf-8")
    seed_metrics = pd.DataFrame(
        [
            {
                "condition": "full",
                "random_seed": 11,
                "run_directory": "run/full/11",
            }
        ]
    )
    seed_metrics.to_csv(suite / "seed_metrics.csv", index=False)
    for filename in (
        "aggregate_metrics.csv",
        "confidence_intervals.csv",
        "paired_comparisons.csv",
        "resource_metrics.csv",
        "offline_metrics.csv",
        "ml_metrics.csv",
    ):
        seed_metrics.to_csv(suite / filename, index=False)
    root = publish_suite(suite, tmp_path / "paper")
    assert (root / "raw" / "interactions.parquet").exists()
    assert (root / "aggregate" / "ablation_comparisons.csv").exists()
    assert json.loads((root / "seed_11" / "run_manifest.json").read_text())["seed"] == 11


def test_weight_sensitivity_reports_stability_and_metrics(tmp_path, monkeypatch) -> None:
    counter = 0

    def fake_run(config: ExperimentConfig) -> Path:
        nonlocal counter
        counter += 1
        directory = tmp_path / f"run-{counter}"
        directory.mkdir()
        variant = config.experiment_name.removeprefix("weight-")
        selected = "changed" if variant == "resource_A" else "baseline"
        pd.DataFrame(
            [
                {
                    "synthetic_learner_id": "a",
                    "step": 0,
                    "selected_activity_id": selected,
                }
            ]
        ).to_parquet(directory / "interactions.parquet", index=False)
        (directory / "summary.json").write_text(
            json.dumps(
                {
                    "mean_synthetic_normalised_gain": 0.2,
                    "mean_synthetic_retention": 0.9,
                    "mean_latency": 2.0,
                    "resource_normalised_utility": 0.1,
                    "config_hash": config.config_hash,
                    "interaction_count": 1,
                }
            ),
            encoding="utf-8",
        )
        return directory

    monkeypatch.setattr("app.evaluation.sensitivity.run_experiment", fake_run)
    config = ExperimentConfig(
        learner_count=1,
        interactions_per_learner=1,
        output_dir=str(tmp_path / "results" / "paper" / "sensitivity_runs"),
        learner_profile_distribution={"mixed": 1.0},
        suite_workers=1,
    )
    output = run_weight_sensitivity(config, [11])
    frame = pd.read_csv(output)
    assert set(frame.variant) >= {"default", "resource_A", "activity_A"}
    assert frame.loc[frame.variant == "default", "recommendation_stability"].iloc[0] == 1.0
    assert frame.loc[frame.variant == "resource_A", "recommendation_stability"].iloc[0] == 0.0
