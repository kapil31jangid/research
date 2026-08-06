"""Dynamic retained-mastery calculations without destructive read updates."""

import math
from datetime import UTC, datetime

from app.learner_model.bkt import clamp_probability


def retained_mastery(
    mastery: float, last_practised_at: datetime | None, forgetting_rate: float
) -> float:
    """Estimate retained mastery using exponential decay at read time only."""
    if forgetting_rate < 0:
        raise ValueError("Forgetting rate cannot be negative")
    if last_practised_at is None:
        return clamp_probability(mastery)
    practice_time = last_practised_at
    if practice_time.tzinfo is None:
        practice_time = practice_time.replace(tzinfo=UTC)
    days = max(0.0, (datetime.now(UTC) - practice_time).total_seconds() / 86_400)
    return clamp_probability(mastery * math.exp(-forgetting_rate * days))


def update_forgetting_rate(current_rate: float, delayed_review_correct: bool) -> float:
    """Make a small bounded rate adjustment from delayed-review evidence."""
    if current_rate < 0:
        raise ValueError("Forgetting rate cannot be negative")
    adjustment = -0.002 if delayed_review_correct else 0.004
    return clamp_probability(max(0.001, current_rate + adjustment))
