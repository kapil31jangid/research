"""Fail-fast integrity checks for synthetic experiment artifacts."""

import numpy as np
import pandas as pd

from app.evaluation.config import ExperimentConfig


def validate_interaction_frame(
    frame: pd.DataFrame,
    config: ExperimentConfig,
) -> dict[str, int | bool]:
    """Validate counts, identity, ranges, and finite measurements for one run."""
    expected = config.learner_count * config.interactions_per_learner
    required = {
        "condition",
        "seed",
        "synthetic_learner_id",
        "step",
        "correct",
        "system_mastery_before",
        "system_mastery_after",
        "synthetic_assessed_mastery_before",
        "synthetic_assessed_mastery_after",
        "resource_score",
        "measured_total_adaptive_latency_ms",
        "data_source",
        "simulated_results",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Interaction output is missing columns: {sorted(missing)}")
    if len(frame) != expected:
        raise ValueError(f"Expected {expected} interactions, found {len(frame)}")
    if frame.synthetic_learner_id.nunique() != config.learner_count:
        raise ValueError("Synthetic learner count does not match configuration")
    if frame.duplicated(["synthetic_learner_id", "step"]).any():
        raise ValueError("Duplicate learner-step interaction detected")
    if set(frame.condition) != {config.condition} or set(frame.seed) != {config.random_seed}:
        raise ValueError("Condition or seed metadata does not match configuration")
    if set(frame.data_source) != {"synthetic"} or not frame.simulated_results.all():
        raise ValueError("Synthetic research-integrity labels are missing")
    bounded = [
        "system_mastery_before",
        "system_mastery_after",
        "synthetic_assessed_mastery_before",
        "synthetic_assessed_mastery_after",
        "retained_mastery",
        "resource_score",
        "misconception_confidence",
    ]
    for column in bounded:
        values = frame[column].dropna().to_numpy(dtype=float)
        if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
            raise ValueError(f"{column} contains a non-finite or out-of-range value")
    nonnegative = [
        "response_time_ms",
        "estimated_computational_cost_ms",
        "measured_controller_latency_ms",
        "measured_recommendation_latency_ms",
        "measured_total_adaptive_latency_ms",
        "bandwidth_kb",
        "memory_used_mb",
    ]
    for column in nonnegative:
        values = frame[column].dropna().to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f"{column} contains a non-finite or negative value")
    probability = frame.selected_candidate_predicted_probability.dropna().to_numpy(dtype=float)
    if not np.isfinite(probability).all() or ((probability < 0) | (probability > 1)).any():
        raise ValueError("Candidate predictions contain invalid probabilities")
    return {
        "expected_interactions": expected,
        "actual_interactions": len(frame),
        "learner_count": frame.synthetic_learner_id.nunique(),
        "duplicate_learner_steps": 0,
        "valid": True,
    }
