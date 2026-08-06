"""Numerically stable learner response-time statistics."""

from math import sqrt

from app.models.learner_state import LearnerConceptState


def update_response_time_statistics(
    state: LearnerConceptState, response_time_ms: int, reference_seconds: float
) -> None:
    """Update running mean and sample variation using Welford's algorithm."""
    seconds = response_time_ms / 1000
    count = state.response_time_count + 1
    delta = seconds - (state.average_response_time or 0.0)
    mean = (state.average_response_time or 0.0) + delta / count
    state.response_time_m2 += delta * (seconds - mean)
    state.response_time_count = count
    state.average_response_time = mean
    standard_deviation = sqrt(state.response_time_m2 / (count - 1)) if count > 1 else 0.0
    state.response_time_variation = min(standard_deviation / reference_seconds, 1.0)
