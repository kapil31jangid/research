"""Independent synthetic outcome generator, deliberately separate from RAPID-Learn ML."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SyntheticResponse:
    correct: bool
    response_time_ms: int
    hints_used: int
    synthetic_true_correct_probability: float


def simulate_response(
    skill: float,
    mastery: float,
    difficulty: float,
    hints: float,
    misconception: float,
    speed: float,
    rng: np.random.Generator,
) -> SyntheticResponse:
    logit = (
        -1.0
        + 2.2 * skill
        + 2.0 * mastery
        - 0.55 * difficulty
        - 1.0 * misconception
        + 0.25 * hints
        + rng.normal(0, 0.25)
    )
    probability = float(1 / (1 + np.exp(-logit)))
    used_hints = int(rng.random() < hints)
    return SyntheticResponse(
        bool(rng.random() < probability),
        int(max(100, rng.lognormal(7.0, 0.35) * speed)),
        used_hints,
        probability,
    )
