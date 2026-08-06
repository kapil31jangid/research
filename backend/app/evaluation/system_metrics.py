"""Latency and host resource summary metrics."""

import numpy as np


def latency_summary(latencies_ms: np.ndarray) -> dict[str, float]:
    if not len(latencies_ms):
        return {"average_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0}
    return {
        "average_ms": float(np.mean(latencies_ms)),
        "p50_ms": float(np.percentile(latencies_ms, 50)),
        "p95_ms": float(np.percentile(latencies_ms, 95)),
    }


def graceful_degradation(full_resource_score: float, constrained_resource_score: float) -> float:
    return constrained_resource_score / full_resource_score if full_resource_score > 0 else 0.0
