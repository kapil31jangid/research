"""Seeded descriptive and bootstrap utilities for synthetic experiments."""

import numpy as np


def bootstrap_confidence_interval(
    values: list[float], seed: int, samples: int = 500
) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    data = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = [rng.choice(data, size=len(data), replace=True).mean() for _ in range(samples)]
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def summary(values: list[float], seed: int) -> dict[str, float]:
    data = np.asarray(values, dtype=float)
    low, high = bootstrap_confidence_interval(values, seed)
    return {
        "mean": float(data.mean()),
        "median": float(np.median(data)),
        "std": float(data.std()),
        "ci_low": low,
        "ci_high": high,
    }
