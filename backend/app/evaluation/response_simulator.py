"""Independent synthetic outcome generator, deliberately separate from RAPID-Learn ML."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SyntheticResponse:
    correct: bool
    response_time_ms: int
    hints_used: int
    synthetic_true_correct_probability: float
    synthetic_misconception_id: str | None = None


def simulate_response(
    skill: float,
    mastery: float,
    difficulty: float,
    hints: float,
    misconception: float | dict[str, float],
    speed: float,
    rng: np.random.Generator,
    guess_probability: float = 0.0,
    slip_probability: float = 0.0,
) -> SyntheticResponse:
    misconception_id = None
    misconception_penalty = float(misconception) if not isinstance(misconception, dict) else 0.0
    if isinstance(misconception, dict) and misconception:
        identifiers = sorted(misconception)
        intensities = np.asarray([misconception[item] for item in identifiers], dtype=float)
        total = float(intensities.sum())
        if total > 0:
            candidate = str(rng.choice(identifiers, p=intensities / total))
            intensity = float(misconception[candidate])
            if rng.random() < intensity:
                misconception_id = candidate
                misconception_penalty = intensity
    logit = (
        -1.0
        + 2.2 * skill
        + 2.0 * mastery
        - 0.55 * difficulty
        - 1.0 * misconception_penalty
        + 0.25 * hints
        + rng.normal(0, 0.25)
    )
    base_probability = float(1 / (1 + np.exp(-logit)))
    probability = float(
        np.clip(
            guess_probability + (1.0 - slip_probability - guess_probability) * base_probability,
            0.0,
            1.0,
        )
    )
    used_hints = int(rng.random() < hints)
    correct = bool(rng.random() < probability)
    return SyntheticResponse(
        correct,
        int(max(100, rng.lognormal(7.0, 0.35) * speed)),
        used_hints,
        probability,
        misconception_id if not correct else None,
    )
