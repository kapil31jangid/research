"""Seeded descriptive, effect-size, and paired bootstrap utilities."""

import numpy as np


def mean(values: list[float]) -> float:
    return float(np.mean(values))


def median(values: list[float]) -> float:
    return float(np.median(values))


def standard_deviation(values: list[float]) -> float:
    return float(np.std(values, ddof=1)) if len(values) > 1 else 0.0


def bootstrap_confidence_interval(
    values: list[float], seed: int, samples: int = 10_000
) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    data = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = rng.choice(data, size=(samples, len(data)), replace=True).mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def paired_bootstrap_difference(
    reference: list[float], comparison: list[float], seed: int, samples: int = 10_000
) -> tuple[float, float, float]:
    if len(reference) != len(comparison) or not reference:
        raise ValueError("paired samples must be non-empty and have equal length")
    differences = np.asarray(reference, dtype=float) - np.asarray(comparison, dtype=float)
    low, high = bootstrap_confidence_interval(differences.tolist(), seed, samples)
    return float(differences.mean()), low, high


def cohens_d(reference: list[float], comparison: list[float]) -> float:
    if len(reference) != len(comparison) or not reference:
        raise ValueError("paired samples must be non-empty and have equal length")
    differences = np.asarray(reference, dtype=float) - np.asarray(comparison, dtype=float)
    deviation = differences.std(ddof=1) if len(differences) > 1 else 0.0
    return float(differences.mean() / deviation) if deviation else 0.0


def summary(values: list[float], seed: int, samples: int = 10_000) -> dict[str, float]:
    low, high = bootstrap_confidence_interval(values, seed, samples)
    return {
        "mean": mean(values),
        "median": median(values),
        "std": standard_deviation(values),
        "ci_low": low,
        "ci_high": high,
    }
