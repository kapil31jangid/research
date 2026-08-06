"""Independent uncertainty estimators for learner knowledge state."""

import math
from collections.abc import Sequence

from app.learner_model.bkt import clamp_probability


def response_time_variation(response_times: Sequence[float]) -> float:
    """Return coefficient-of-variation normalised to [0, 1]."""
    positive_times = [time for time in response_times if time > 0]
    if len(positive_times) < 2:
        return 0.0
    mean = sum(positive_times) / len(positive_times)
    variance = sum((time - mean) ** 2 for time in positive_times) / len(positive_times)
    return clamp_probability(math.sqrt(variance) / mean)


def heuristic_uncertainty(
    attempts: int, recent_correctness: Sequence[bool], response_time_variability: float
) -> float:
    """Combine evidence, consistency, and response-time uncertainty."""
    evidence = 1.0 / math.sqrt(max(attempts, 0) + 1)
    consistency = (
        1.0 - (sum(recent_correctness) / len(recent_correctness)) if recent_correctness else 1.0
    )
    return clamp_probability(
        0.50 * evidence + 0.35 * consistency + 0.15 * clamp_probability(response_time_variability)
    )


def entropy_uncertainty(mastery: float) -> float:
    """Binary entropy in bits, normalised to [0, 1]."""
    probability = clamp_probability(mastery)
    if probability in {0.0, 1.0}:
        return 0.0
    return -(
        probability * math.log2(probability) + (1.0 - probability) * math.log2(1.0 - probability)
    )


def calculate_uncertainty(
    mode: str,
    mastery: float,
    attempts: int,
    recent_correctness: Sequence[bool],
    response_time_variability: float,
) -> float:
    """Select heuristic, entropy, or evenly weighted combined uncertainty."""
    heuristic = heuristic_uncertainty(attempts, recent_correctness, response_time_variability)
    entropy = entropy_uncertainty(mastery)
    if mode == "heuristic":
        return heuristic
    if mode == "entropy":
        return entropy
    if mode == "combined":
        return (heuristic + entropy) / 2.0
    raise ValueError(f"Unsupported uncertainty mode: {mode}")
