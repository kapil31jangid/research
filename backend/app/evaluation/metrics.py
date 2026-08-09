"""Auditable learner and condition metrics for explicitly synthetic runs."""

import json

import numpy as np
import pandas as pd

from app.evaluation.resource_metrics import resource_normalised_learning_utility


def _safe_mean(series: pd.Series) -> float | None:
    values = series.dropna()
    return float(values.mean()) if not values.empty else None


def learner_metrics(
    interactions: pd.DataFrame,
    concept_outcomes: pd.DataFrame,
    mastery_threshold: float,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for learner_id, group in interactions.groupby("synthetic_learner_id"):
        ordered = group.sort_values("step")
        concepts = concept_outcomes.loc[concept_outcomes.synthetic_learner_id == learner_id]
        threshold = ordered.loc[ordered.system_mean_mastery_after >= mastery_threshold, "step"]
        paths = ordered.actual_adaptation_path
        synthetic_triggered = int(ordered.synthetic_true_misconception_id.notna().sum())
        resolved = int(ordered.synthetic_misconception_resolved.sum())
        system_detected = int(ordered.system_detected_misconception_id.notna().sum())
        remediation = ordered.actual_adaptation_path.eq("misconception_remediation")
        matched = int(ordered.synthetic_misconception_matched_remediation.sum())
        unmatched = int((remediation & ~ordered.synthetic_misconception_matched_remediation).sum())
        costs = ordered.estimated_computational_cost_ms.astype(float)
        latencies = ordered.measured_total_adaptive_latency_ms.astype(float)
        initial_mean = float(concepts.initial_system_mastery.mean())
        final_mean = float(concepts.final_system_mastery.mean())
        initial_synthetic = float(concepts.initial_synthetic_mastery.mean())
        final_synthetic = float(concepts.final_synthetic_mastery.mean())
        system_normalised_gain = float(
            (
                (concepts.final_system_mastery - concepts.initial_system_mastery)
                / (1.0 - concepts.initial_system_mastery).clip(lower=1e-9)
            ).mean()
        )
        synthetic_normalised_gain = float(
            (
                (concepts.final_synthetic_mastery - concepts.initial_synthetic_mastery)
                / (1.0 - concepts.initial_synthetic_mastery).clip(lower=1e-9)
            ).mean()
        )
        retention = (
            float(
                (
                    ordered.retained_mastery.astype(float)
                    / ordered.system_mastery_before.astype(float).clip(lower=1e-9)
                )
                .clip(upper=1.0)
                .mean()
            )
            if {"retained_mastery", "system_mastery_before"} <= set(ordered.columns)
            else 1.0
        )
        synthetic_retention = (
            float(
                (
                    ordered.synthetic_retained_mastery_before.astype(float)
                    / ordered.synthetic_assessed_mastery_before.astype(float).clip(lower=1e-9)
                )
                .clip(upper=1.0)
                .mean()
            )
            if "synthetic_retained_mastery_before" in ordered
            else 1.0
        )
        memory_pressure = (
            float(
                (
                    1.0
                    - ordered.available_memory_mb.astype(float)
                    / ordered.total_memory_mb.astype(float).clip(lower=1e-9)
                ).mean()
            )
            if "available_memory_mb" in ordered
            else 0.0
        )
        cpu_fraction = (
            float(ordered.cpu_percent.astype(float).mean() / 100.0)
            if "cpu_percent" in ordered
            else 0.0
        )
        mean_bandwidth = (
            float(ordered.bandwidth_kb.astype(float).mean()) if "bandwidth_kb" in ordered else 0.0
        )
        mean_memory_used_mb = (
            float(ordered.memory_used_mb.astype(float).mean())
            if "memory_used_mb" in ordered
            else 0.0
        )
        rows.append(
            {
                "synthetic_learner_id": learner_id,
                "initial_mean_mastery": initial_mean,
                "final_mean_mastery": final_mean,
                "mastery_gain": final_mean - initial_mean,
                "response_accuracy": (
                    float(ordered.correct.mean()) if "correct" in ordered else None
                ),
                "normalised_gain": system_normalised_gain,
                "retention": retention,
                "synthetic_retention": synthetic_retention,
                "initial_mean_synthetic_mastery": initial_synthetic,
                "final_mean_synthetic_mastery": final_synthetic,
                "synthetic_mastery_gain": final_synthetic - initial_synthetic,
                "synthetic_normalised_gain": synthetic_normalised_gain,
                "concepts_mastered": int(
                    (concepts.final_system_mastery >= mastery_threshold).sum()
                ),
                "mastery_threshold_success": final_mean >= mastery_threshold,
                "interactions_to_mastery_threshold": (
                    int(threshold.iloc[0] + 1) if len(threshold) else None
                ),
                "synthetic_misconceptions_triggered": synthetic_triggered,
                "synthetic_misconceptions_resolved": resolved,
                "synthetic_misconception_resolution_rate": (
                    resolved / synthetic_triggered if synthetic_triggered else None
                ),
                "system_misconceptions_detected": system_detected,
                "matched_remediation_count": matched,
                "unmatched_remediation_count": unmatched,
                "misconceptions_triggered": synthetic_triggered,
                "misconceptions_resolved": resolved,
                "misconception_resolution_rate": (
                    resolved / synthetic_triggered if synthetic_triggered else None
                ),
                "mean_response_time": float(ordered.response_time_ms.mean()),
                "mean_resource_score": float(ordered.resource_score.mean()),
                "mean_memory_pressure": memory_pressure,
                "mean_memory_used_mb": mean_memory_used_mb,
                "mean_cpu_percent": cpu_fraction * 100.0,
                "mean_bandwidth_kb": mean_bandwidth,
                "resource_normalised_utility": resource_normalised_learning_utility(
                    synthetic_normalised_gain,
                    float(latencies.mean()),
                    memory_pressure,
                    cpu_fraction,
                    mean_bandwidth,
                ),
                "offline_interaction_rate": float(ordered.offline.mean()),
                "offline_recommendation_availability": (
                    float(
                        ordered.loc[
                            ordered.offline.astype(bool), "offline_content_available"
                        ].mean()
                    )
                    if ordered.offline.astype(bool).any() and "offline_content_available" in ordered
                    else None
                ),
                "prerequisite_violation_rate": (
                    float(
                        ordered.loc[
                            ordered.prerequisite_gap_present.astype(bool),
                            "prerequisite_violation",
                        ].mean()
                    )
                    if "prerequisite_gap_present" in ordered
                    and ordered.prerequisite_gap_present.astype(bool).any()
                    else None
                ),
                "fallback_rate": float(ordered.fallback_used.mean()),
                "ml_path_rate": float((paths == "lightweight_ml_recommendation").mean()),
                "bkt_path_rate": float((paths == "bkt_based_recommendation").mean()),
                "cached_path_rate": float((paths == "cached_offline_recommendation").mean()),
                "mean_adaptive_latency_ms": float(latencies.mean()),
                "p95_adaptive_latency_ms": float(np.percentile(latencies, 95)),
                "estimated_total_compute_cost_ms": float(costs.sum()),
                "mean_estimated_compute_cost_ms": float(costs.mean()),
            }
        )
    return pd.DataFrame(rows)


def condition_metrics(
    interactions: pd.DataFrame,
    concept_outcomes: pd.DataFrame,
    mastery_threshold: float,
) -> dict[str, object]:
    learners = learner_metrics(interactions, concept_outcomes, mastery_threshold)
    latency = interactions.measured_total_adaptive_latency_ms.to_numpy(dtype=float)
    costs = interactions.estimated_computational_cost_ms.to_numpy(dtype=float)
    paths = interactions.actual_adaptation_path
    events = interactions.event_code
    threshold_steps = learners.interactions_to_mastery_threshold.dropna()
    synthetic_triggered = int(interactions.synthetic_true_misconception_id.notna().sum())
    synthetic_resolved = int(interactions.synthetic_misconception_resolved.sum())
    remediation = interactions.actual_adaptation_path.eq("misconception_remediation")
    matched_remediation = int(interactions.synthetic_misconception_matched_remediation.sum())
    remediation_count = int(remediation.sum())
    system_detected = int(interactions.system_detected_misconception_id.notna().sum())
    offline = interactions.offline.astype(bool)
    offline_misses = events.eq("offline_content_miss") & offline
    return {
        "response_accuracy": (
            float(interactions.correct.mean()) if "correct" in interactions else None
        ),
        "mean_initial_mastery": float(learners.initial_mean_mastery.mean()),
        "mean_final_mastery": float(learners.final_mean_mastery.mean()),
        "mean_mastery_gain": float(learners.mastery_gain.mean()),
        "mean_normalised_gain": float(learners.normalised_gain.mean()),
        "mean_retention": float(learners.retention.mean()),
        "mean_synthetic_retention": float(learners.synthetic_retention.mean()),
        "median_interactions_to_threshold": (
            float(threshold_steps.median()) if not threshold_steps.empty else None
        ),
        "mastery_threshold_success_rate": float(learners.mastery_threshold_success.mean()),
        "mean_initial_synthetic_mastery": float(learners.initial_mean_synthetic_mastery.mean()),
        "mean_final_synthetic_mastery": float(learners.final_mean_synthetic_mastery.mean()),
        "mean_synthetic_mastery_gain": float(learners.synthetic_mastery_gain.mean()),
        "mean_synthetic_normalised_gain": float(learners.synthetic_normalised_gain.mean()),
        "synthetic_misconception_resolution_rate": (
            synthetic_resolved / synthetic_triggered if synthetic_triggered else None
        ),
        "misconception_resolution_rate": (
            synthetic_resolved / synthetic_triggered if synthetic_triggered else None
        ),
        "matched_remediation_rate": (
            matched_remediation / remediation_count if remediation_count else None
        ),
        "system_detection_rate": system_detected / len(interactions),
        "path_distribution": paths.value_counts(normalize=True).to_dict(),
        "fallback_rate": float(interactions.fallback_used.mean()),
        "ml_usage_rate": float((paths == "lightweight_ml_recommendation").mean()),
        "offline_adaptation_rate": float((paths == "cached_offline_recommendation").mean()),
        "mean_resource_score": float(interactions.resource_score.mean()),
        "mean_memory_pressure": _safe_mean(learners.mean_memory_pressure),
        "mean_memory_used_mb": _safe_mean(learners.mean_memory_used_mb),
        "mean_cpu_percent": _safe_mean(learners.mean_cpu_percent),
        "mean_bandwidth_kb": _safe_mean(learners.mean_bandwidth_kb),
        "resource_normalised_utility": _safe_mean(learners.resource_normalised_utility),
        "prerequisite_violation_rate": _safe_mean(learners.prerequisite_violation_rate),
        "offline_recommendation_availability": _safe_mean(
            learners.offline_recommendation_availability
        ),
        "mean_controller_latency_ms": float(interactions.measured_controller_latency_ms.mean())
        if "measured_controller_latency_ms" in interactions
        else None,
        "mean_recommendation_latency_ms": float(
            interactions.measured_recommendation_latency_ms.mean()
        )
        if "measured_recommendation_latency_ms" in interactions
        else None,
        "mean_estimated_compute_cost_ms": float(costs.mean()),
        "median_estimated_compute_cost_ms": float(np.median(costs)),
        "total_estimated_compute_cost_ms": float(costs.sum()),
        "mean_latency": float(latency.mean()),
        "p50_latency": float(np.percentile(latency, 50)),
        "p95_latency": float(np.percentile(latency, 95)),
        "p99_latency": float(np.percentile(latency, 99)),
        "recommendation_failure_rate": float(events.eq("recommendation_failure").mean()),
        "no_candidate_rate": float(events.eq("no_candidate").mean()),
        "model_unavailable_rate": float(events.eq("model_unavailable").mean()),
        "offline_content_miss_rate": (
            float(offline_misses.sum() / offline.sum()) if offline.any() else None
        ),
        "matching_offline_activity_count": int(
            interactions.matching_offline_activity_ids.map(
                lambda value: len(json.loads(value))
            ).sum()
        ),
    }
