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
from app.evaluation.metrics import condition_metrics, learner_metrics
from app.evaluation.plots import write_plots
from app.evaluation.provenance import collect_provenance
from app.evaluation.resource_simulator import simulate_resource
from app.evaluation.response_simulator import simulate_response
from app.evaluation.synthetic_learners import generate_learners
from app.evaluation.tables import write_condition_table
from app.models.learner import Learner
from app.models.learner_state import LearnerConceptState
from app.models.question import Question
from app.schemas.interactions import InteractionCreate
from app.services.interaction_service import process_interaction


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
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with factory() as db:
        seed_database(db)
        questions = list(db.scalars(select(Question).order_by(Question.id)))
        concept_ids = sorted({question.concept_id for question in questions})
        learners = generate_learners(
            config.learner_count,
            concept_ids,
            config.random_seed,
            config.learner_profile_distribution,
        )
        rows: list[dict[str, object]] = []
        for learner_index, synthetic in enumerate(learners):
            learner = Learner(
                id=synthetic.synthetic_learner_id,
                name=synthetic.synthetic_learner_id,
                age_group="synthetic",
                grade=0,
                device_profile=synthetic.resource_profile,
            )
            db.add(learner)
            db.commit()
            for step in range(config.interactions_per_learner):
                question = questions[
                    (learner_index * config.interactions_per_learner + step) % len(questions)
                ]
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
                mastery = (
                    state.mastery_probability
                    if state
                    else synthetic.initial_mastery_by_concept[question.concept_id]
                )
                response = simulate_response(
                    synthetic.latent_skill,
                    mastery,
                    question.difficulty,
                    synthetic.hint_probability,
                    synthetic.misconception_tendency,
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
                result = process_interaction(payload, question, db)
                recommendation = result.recommendation
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
                        "mastery_after": result.learner_state.mastery_probability,
                        "retained_mastery": result.learner_state.retained_mastery,
                        "uncertainty": result.learner_state.uncertainty,
                        "resource_score": resource.score,
                        "offline": resource.offline,
                        "requested_adaptation_path": recommendation.requested_adaptation_path,
                        "actual_adaptation_path": recommendation.adaptation_path,
                        "fallback_used": recommendation.fallback_used,
                        "selected_activity_id": recommendation.selected_activity_id,
                        "offline_content_reason": recommendation.offline_content_reason,
                        "selected_candidate_predicted_probability": selected_probability,
                        "measured_total_adaptive_latency_ms": adaptive_latency,
                        "synthetic_latent_skill": synthetic.latent_skill,
                        "synthetic_true_correct_probability": true_probability,
                        "data_source": "synthetic",
                    }
                )
    interactions = pd.DataFrame(rows)
    interactions.to_parquet(directory / "interactions.parquet", index=False)
    interactions.to_csv(directory / "interactions.csv", index=False)
    learners_frame = learner_metrics(interactions, config.mastery_threshold)
    learners_frame.to_parquet(directory / "learners.parquet", index=False)
    learners_frame.to_csv(directory / "learners.csv", index=False)
    summary = {
        "simulated_results": True,
        "data_source": "synthetic",
        "condition": config.condition,
        "interaction_count": len(rows),
        "mean_correct": float(interactions.correct.mean()),
        **condition_metrics(interactions, config.mastery_threshold),
    }
    (directory / "config.json").write_text(config.model_dump_json(indent=2), encoding="utf-8")
    (directory / "provenance.json").write_text(
        json.dumps(collect_provenance(), indent=2), encoding="utf-8"
    )
    (directory / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_condition_table(interactions, directory)
    write_plots(interactions, directory)
    return directory
