"""Learner and condition metrics for explicitly synthetic runs."""

import numpy as np
import pandas as pd


def learner_metrics(interactions: pd.DataFrame, mastery_threshold: float) -> pd.DataFrame:
    rows = []
    for learner_id, group in interactions.groupby("synthetic_learner_id"):
        ordered = group.sort_values("step")
        threshold = ordered.loc[ordered.mastery_after >= mastery_threshold, "step"]
        paths = ordered.actual_adaptation_path
        rows.append(
            {
                "synthetic_learner_id": learner_id,
                "initial_mean_mastery": float(ordered.mastery_after.iloc[0]),
                "final_mean_mastery": float(ordered.mastery_after.iloc[-1]),
                "mastery_gain": float(
                    ordered.mastery_after.iloc[-1] - ordered.mastery_after.iloc[0]
                ),
                "interactions_to_mastery_threshold": int(threshold.iloc[0] + 1)
                if len(threshold)
                else None,
                "mean_response_time": float(ordered.response_time_ms.mean()),
                "mean_resource_score": float(ordered.resource_score.mean()),
                "offline_interaction_rate": float(ordered.offline.mean()),
                "fallback_rate": float(ordered.fallback_used.mean()),
                "ml_path_rate": float((paths == "lightweight_ml_recommendation").mean()),
                "bkt_path_rate": float((paths == "bkt_based_recommendation").mean()),
                "cached_path_rate": float((paths == "cached_offline_recommendation").mean()),
                "mean_adaptive_latency_ms": float(
                    ordered.measured_total_adaptive_latency_ms.mean()
                ),
            }
        )
    return pd.DataFrame(rows)


def condition_metrics(interactions: pd.DataFrame, mastery_threshold: float) -> dict[str, object]:
    learner = learner_metrics(interactions, mastery_threshold)
    latency = interactions.measured_total_adaptive_latency_ms.to_numpy(dtype=float)
    return {
        "mean_final_mastery": float(learner.final_mean_mastery.mean()),
        "mean_mastery_gain": float(learner.mastery_gain.mean()),
        "mastery_threshold_success_rate": float(
            learner.interactions_to_mastery_threshold.notna().mean()
        ),
        "fallback_rate": float(interactions.fallback_used.mean()),
        "path_distribution": interactions.actual_adaptation_path.value_counts(
            normalize=True
        ).to_dict(),
        "mean_latency": float(latency.mean()),
        "p50_latency": float(np.percentile(latency, 50)),
        "p95_latency": float(np.percentile(latency, 95)),
        "p99_latency": float(np.percentile(latency, 99)),
    }
