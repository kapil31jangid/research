"""Auditable learner and condition metrics for explicitly synthetic runs."""

import json

import numpy as np
import pandas as pd


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
        rows.append(
            {
                "synthetic_learner_id": learner_id,
                "initial_mean_mastery": initial_mean,
                "final_mean_mastery": final_mean,
                "mastery_gain": final_mean - initial_mean,
                "initial_mean_synthetic_mastery": initial_synthetic,
                "final_mean_synthetic_mastery": final_synthetic,
                "synthetic_mastery_gain": final_synthetic - initial_synthetic,
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
                "offline_interaction_rate": float(ordered.offline.mean()),
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
        "mean_initial_mastery": float(learners.initial_mean_mastery.mean()),
        "mean_final_mastery": float(learners.final_mean_mastery.mean()),
        "mean_mastery_gain": float(learners.mastery_gain.mean()),
        "median_interactions_to_threshold": (
            float(threshold_steps.median()) if not threshold_steps.empty else None
        ),
        "mastery_threshold_success_rate": float(learners.mastery_threshold_success.mean()),
        "mean_initial_synthetic_mastery": float(learners.initial_mean_synthetic_mastery.mean()),
        "mean_final_synthetic_mastery": float(learners.final_mean_synthetic_mastery.mean()),
        "mean_synthetic_mastery_gain": float(learners.synthetic_mastery_gain.mean()),
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
