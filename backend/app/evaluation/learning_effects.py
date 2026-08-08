"""Independent synthetic learning effects for recommended activities."""

import numpy as np


def apply_learning_effect(
    mastery: float, difficulty: float, relevant: bool, rng: np.random.Generator
) -> float:
    """Update simulator-only latent mastery without using BKT or ML scores."""
    match = 1.0 - min(abs(mastery - difficulty / 4.0), 1.0)
    gain = (0.025 + 0.045 * match) * (1.0 if relevant else 0.3) + rng.normal(0, 0.005)
    return float(np.clip(mastery + gain, 0.0, 1.0))


def apply_recommendation_learning(
    latent_mastery: dict[str, float],
    assessed_concept_id: str,
    selected_concept_id: str,
    difficulty: float,
    rng: np.random.Generator,
) -> tuple[float, float]:
    """Mutate only the recommendation-selected concept and return its before/after."""
    before = latent_mastery[selected_concept_id]
    after = apply_learning_effect(
        before, difficulty, selected_concept_id == assessed_concept_id, rng
    )
    latent_mastery[selected_concept_id] = after
    return before, after


def apply_misconception_remediation(intensity: float, matched: bool) -> float:
    """Model a simulator-only reduction for correctly matched remediation."""
    return max(0.0, intensity * 0.5) if matched else intensity
