"""Isolated, reproducible synthetic evaluation using the real interaction service."""

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database.base import Base
from app.database.seed import seed_database
from app.evaluation.config import ExperimentConfig
from app.evaluation.learning_effects import (
    apply_misconception_remediation,
    apply_recommendation_learning,
)
from app.evaluation.metrics import condition_metrics, learner_metrics
from app.evaluation.ml_metrics import synthetic_ml_metrics
from app.evaluation.plots import write_plots
from app.evaluation.policy import evaluation_policy_from_config
from app.evaluation.provenance import collect_provenance
from app.evaluation.resource_simulator import simulate_resource
from app.evaluation.response_simulator import simulate_response
from app.evaluation.synthetic_learners import generate_learners
from app.evaluation.tables import write_condition_table
from app.misconceptions.rules import MisconceptionRule, load_rules
from app.models.activity import LearningActivity
from app.models.learner import Learner
from app.models.learner_state import LearnerConceptState
from app.models.question import Question
from app.schemas.interactions import InteractionCreate
from app.services.interaction_service import process_interaction


def misconception_ids_by_concept(
    rules: list[MisconceptionRule],
) -> dict[str, tuple[str, ...]]:
    """Map curriculum concepts to deterministic identifiers from real rules."""
    mapping: dict[str, set[str]] = {}
    for rule in rules:
        for concept_id in rule.concept_ids:
            mapping.setdefault(concept_id, set()).add(rule.id)
    return {concept_id: tuple(sorted(identifiers)) for concept_id, identifiers in mapping.items()}


def run_experiment(config: ExperimentConfig) -> Path:
    """Run one condition in a fresh SQLite database and write synthetic artifacts."""
    experiment_id = f"{datetime.now(UTC):%Y-%m-%d}_{config.condition}_seed{config.random_seed}"
    directory = Path(config.output_dir) / experiment_id
    suffix = 1
    while directory.exists():
        directory = Path(config.output_dir) / f"{experiment_id}_{suffix:02d}"
        suffix += 1
    directory.mkdir(parents=True)
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    # Experiment sessions retain loaded values across each interaction commit. The
    # production service still commits and refreshes its persisted records; avoiding
    # blanket ORM expiry here prevents thousands of redundant SQLite point queries.
    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    with factory() as db:
        seed_database(db)
        questions = list(db.scalars(select(Question).order_by(Question.id)))
        concept_ids = sorted({question.concept_id for question in questions})
        misconception_ids = misconception_ids_by_concept(load_rules())
        learners = generate_learners(
            config.learner_count,
            concept_ids,
            config.random_seed,
            config.learner_profile_distribution,
        )
        rows: list[dict[str, object]] = []
        concept_rows: list[dict[str, object]] = []
        for learner_index, synthetic in enumerate(learners):
            latent_mastery = dict(synthetic.initial_mastery_by_concept)
            initial_system_mastery = dict(synthetic.initial_mastery_by_concept)
            synthetic_misconceptions = {
                misconception_id: synthetic.misconception_tendency
                for concept_id in concept_ids
                for misconception_id in misconception_ids.get(concept_id, ())
            }
            next_concept_id: str | None = None
            learner = Learner(
                id=synthetic.synthetic_learner_id,
                name=synthetic.synthetic_learner_id,
                age_group="synthetic",
                grade=0,
                device_profile=synthetic.resource_profile,
            )
            db.add(learner)
            for concept_id in concept_ids:
                db.add(
                    LearnerConceptState(
                        learner_id=learner.id,
                        concept_id=concept_id,
                        mastery_probability=synthetic.initial_mastery_by_concept[concept_id],
                        uncertainty=0.5,
                        attempts=0,
                        correct_attempts=0,
                        recent_correctness="[]",
                        response_time_variation=0.0,
                        response_time_m2=0.0,
                        response_time_count=0,
                        hint_usage_rate=0.0,
                        forgetting_rate=synthetic.forgetting_factor,
                    )
                )
            db.commit()
            for step in range(config.interactions_per_learner):
                eligible = [item for item in questions if item.concept_id == next_concept_id]
                question = (
                    eligible[step % len(eligible)]
                    if eligible and config.enable_adaptation
                    else questions[
                        (learner_index * config.interactions_per_learner + step) % len(questions)
                        if config.enable_adaptation
                        else step % len(questions)
                    ]
                )
                resource_profile = (
                    "high_end"
                    if not config.enable_resource_awareness
                    else synthetic.resource_profile
                )
                resource = simulate_resource(
                    resource_profile,
                    np.random.default_rng(config.random_seed + learner_index * 1000 + step),
                    step,
                )
                state = next(
                    (
                        item
                        for item in db.scalars(
                            select(LearnerConceptState).where(
                                LearnerConceptState.learner_id == learner.id,
                                LearnerConceptState.concept_id == question.concept_id,
                            )
                        )
                    ),
                    None,
                )
                system_mastery_before = (
                    state.mastery_probability
                    if state
                    else synthetic.initial_mastery_by_concept[question.concept_id]
                )
                synthetic_assessed_mastery_before = latent_mastery[question.concept_id]
                current_misconceptions = {
                    misconception_id: synthetic_misconceptions[misconception_id]
                    for misconception_id in misconception_ids.get(question.concept_id, ())
                }
                response = simulate_response(
                    synthetic.latent_skill,
                    synthetic_assessed_mastery_before,
                    question.difficulty,
                    synthetic.hint_probability,
                    current_misconceptions,
                    synthetic.response_speed_factor,
                    np.random.default_rng(config.random_seed + learner_index * 10000 + step),
                )
                submitted = question.correct_answer if response.correct else "0"
                payload = InteractionCreate(
                    learner_id=learner.id,
                    question_id=question.id,
                    submitted_answer=submitted,
                    response_time_ms=response.response_time_ms,
                    hints_used=response.hints_used,
                    offline=resource.offline if config.enable_offline_adaptation else False,
                    device_resource_state={
                        key: getattr(resource, key)
                        for key in (
                            "available_memory_mb",
                            "total_memory_mb",
                            "cpu_percent",
                            "battery_percent",
                            "battery_charging",
                            "network_available",
                            "network_quality",
                            "storage_available_mb",
                            "inference_latency_ms",
                        )
                    },
                )
                result = process_interaction(
                    payload, question, db, evaluation_policy_from_config(config)
                )
                recommendation = result.recommendation
                synthetic_misconception_id = response.synthetic_misconception_id
                synthetic_misconception_before = (
                    synthetic_misconceptions[synthetic_misconception_id]
                    if synthetic_misconception_id is not None
                    else None
                )
                synthetic_misconception_after = synthetic_misconception_before
                matched_remediation = False
                activity = db.get(LearningActivity, recommendation.selected_activity_id)
                selected_concept = recommendation.selected_concept_id
                synthetic_selected_mastery_before = latent_mastery[selected_concept]
                synthetic_selected_mastery_after = synthetic_selected_mastery_before
                if activity is not None:
                    (
                        synthetic_selected_mastery_before,
                        synthetic_selected_mastery_after,
                    ) = apply_recommendation_learning(
                        latent_mastery,
                        question.concept_id,
                        selected_concept,
                        activity.difficulty,
                        np.random.default_rng(config.random_seed + learner_index * 20_000 + step),
                    )
                    eligible_activity_misconceptions = (
                        set(json.loads(activity.misconception_ids))
                        if config.enable_misconceptions
                        and recommendation.adaptation_path == "misconception_remediation"
                        else set()
                    )
                    (
                        synthetic_misconception_before,
                        synthetic_misconception_after,
                        matched_remediation,
                    ) = apply_misconception_remediation(
                        synthetic_misconceptions,
                        synthetic_misconception_id,
                        eligible_activity_misconceptions,
                    )
                    next_concept_id = selected_concept if config.enable_adaptation else None
                all_states = list(
                    db.scalars(
                        select(LearnerConceptState).where(
                            LearnerConceptState.learner_id == learner.id
                        )
                    )
                )
                selected_probability = recommendation.selected_candidate_predicted_probability
                adaptive_latency = recommendation.measured_total_adaptive_latency_ms
                true_probability = response.synthetic_true_correct_probability
                rows.append(
                    {
                        "experiment_id": experiment_id,
                        "condition": config.condition,
                        "seed": config.random_seed,
                        "synthetic_learner_id": learner.id,
                        "learner_profile": synthetic.profile,
                        "step": step,
                        "question_id": question.id,
                        "concept_id": question.concept_id,
                        "correct": result.interaction.correct,
                        "response_time_ms": response.response_time_ms,
                        "hints_used": response.hints_used,
                        "system_mastery_before": system_mastery_before,
                        "system_mastery_after": result.learner_state.mastery_probability,
                        "system_mean_mastery_after": float(
                            np.mean([item.mastery_probability for item in all_states])
                        ),
                        "synthetic_assessed_concept_id": question.concept_id,
                        "synthetic_assessed_mastery_before": synthetic_assessed_mastery_before,
                        "synthetic_assessed_mastery_after": latent_mastery[question.concept_id],
                        "synthetic_selected_concept_id": selected_concept,
                        "synthetic_selected_mastery_before": synthetic_selected_mastery_before,
                        "synthetic_selected_mastery_after": synthetic_selected_mastery_after,
                        "retained_mastery": (
                            result.learner_state.retained_mastery
                            if config.enable_forgetting
                            else result.learner_state.mastery_probability
                        ),
                        "uncertainty": result.learner_state.uncertainty,
                        "misconception_id": result.misconception.id,
                        "system_detected_misconception_id": result.misconception.id,
                        "misconception_confidence": result.misconception.confidence,
                        "synthetic_true_misconception_id": synthetic_misconception_id,
                        "synthetic_misconception_id": synthetic_misconception_id,
                        "synthetic_misconception_before": synthetic_misconception_before,
                        "synthetic_misconception_after": synthetic_misconception_after,
                        "synthetic_misconception_matched_remediation": matched_remediation,
                        "synthetic_misconception_resolved": (
                            synthetic_misconception_before is not None
                            and synthetic_misconception_after is not None
                            and synthetic_misconception_before
                            >= config.synthetic_misconception_resolution_threshold
                            and synthetic_misconception_after
                            < config.synthetic_misconception_resolution_threshold
                        ),
                        "resource_score": resource.score,
                        "resource_profile": resource_profile,
                        "network_available": resource.network_available,
                        "network_quality": resource.network_quality,
                        "offline": resource.offline,
                        "requested_adaptation_path": recommendation.requested_adaptation_path,
                        "actual_adaptation_path": recommendation.adaptation_path,
                        "fallback_used": recommendation.fallback_used,
                        "fallback_reason": recommendation.fallback_reason,
                        "selected_concept_id": selected_concept,
                        "selected_activity_id": recommendation.selected_activity_id,
                        "selected_activity_type": activity.activity_type if activity else None,
                        "selected_activity_difficulty": activity.difficulty if activity else None,
                        "offline_content_available": recommendation.offline_content_available,
                        "matching_offline_activity_ids": json.dumps(
                            recommendation.matching_offline_activity_ids
                        ),
                        "offline_content_reason": recommendation.offline_content_reason,
                        "ml_model_available": recommendation.ml_model_available,
                        "model_version": recommendation.model_version,
                        "selected_candidate_predicted_probability": selected_probability,
                        "estimated_computational_cost_ms": recommendation.computational_cost_ms,
                        "measured_controller_latency_ms": (
                            recommendation.measured_controller_latency_ms
                        ),
                        "measured_recommendation_latency_ms": (
                            recommendation.measured_recommendation_latency_ms
                        ),
                        "measured_total_adaptive_latency_ms": adaptive_latency,
                        "synthetic_latent_skill": synthetic.latent_skill,
                        "synthetic_true_correct_probability": true_probability,
                        "data_source": "synthetic",
                        "simulated_results": True,
                        "event_code": (
                            "fallback"
                            if recommendation.fallback_used
                            else "model_unavailable"
                            if config.enable_ml and not recommendation.ml_model_available
                            else "offline_content_miss"
                            if resource.offline and not recommendation.offline_content_available
                            else "recommendation_success"
                        ),
                    }
                )
            final_states = {
                item.concept_id: item
                for item in db.scalars(
                    select(LearnerConceptState).where(LearnerConceptState.learner_id == learner.id)
                )
            }
            for concept_id in concept_ids:
                initial_system = initial_system_mastery[concept_id]
                final_system = final_states[concept_id].mastery_probability
                initial_synthetic = synthetic.initial_mastery_by_concept[concept_id]
                final_synthetic = latent_mastery[concept_id]
                concept_rows.append(
                    {
                        "experiment_id": experiment_id,
                        "condition": config.condition,
                        "seed": config.random_seed,
                        "synthetic_learner_id": learner.id,
                        "concept_id": concept_id,
                        "initial_system_mastery": initial_system,
                        "final_system_mastery": final_system,
                        "system_mastery_gain": final_system - initial_system,
                        "initial_synthetic_mastery": initial_synthetic,
                        "final_synthetic_mastery": final_synthetic,
                        "synthetic_mastery_gain": final_synthetic - initial_synthetic,
                        "mastery_threshold_reached": final_system >= config.mastery_threshold,
                    }
                )
    engine.dispose()
    interactions = pd.DataFrame(rows)
    interactions.to_parquet(directory / "interactions.parquet", index=False)
    interactions.to_csv(directory / "interactions.csv", index=False)
    concept_outcomes = pd.DataFrame(concept_rows)
    concept_outcomes.to_parquet(directory / "concept_outcomes.parquet", index=False)
    concept_outcomes.to_csv(directory / "concept_outcomes.csv", index=False)
    learners_frame = learner_metrics(interactions, concept_outcomes, config.mastery_threshold)
    learners_frame.to_parquet(directory / "learners.parquet", index=False)
    learners_frame.to_csv(directory / "learners.csv", index=False)
    summary = {
        "simulated_results": True,
        "data_source": "synthetic",
        "condition": config.condition,
        "interaction_count": len(rows),
        "mean_correct": float(interactions.correct.mean()),
        "project": "RAPID-Learn",
        "experiment_id": experiment_id,
        "random_seed": config.random_seed,
        "config_hash": config.config_hash,
        "bootstrap_samples": config.bootstrap_samples,
        "educational_effectiveness_validated": False,
        **condition_metrics(interactions, concept_outcomes, config.mastery_threshold),
        **synthetic_ml_metrics(interactions),
    }
    (directory / "config.json").write_text(config.model_dump_json(indent=2), encoding="utf-8")
    (directory / "provenance.json").write_text(
        json.dumps(
            collect_provenance()
            | {
                "config_hash": config.config_hash,
                "condition": config.condition,
                "seed": config.random_seed,
                "bootstrap_samples": config.bootstrap_samples,
                "experiment_harness_version": "2",
                "simulated_results": True,
                "data_source": "synthetic",
                "educational_effectiveness_validated": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (directory / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_condition_table(interactions, directory)
    write_plots(interactions, directory)
    return directory
