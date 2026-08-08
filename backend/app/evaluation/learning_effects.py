"""Independent synthetic learning effects for recommended activities."""

import numpy as np


def apply_learning_effect(
    mastery: float, difficulty: float, relevant: bool, rng: np.random.Generator
) -> float:
    """Update simulator-only latent mastery without using BKT or ML scores."""
    match = 1.0 - min(abs(mastery - difficulty / 4.0), 1.0)
    gain = (0.025 + 0.045 * match) * (1.0 if relevant else 0.3) + rng.normal(0, 0.005)
    return float(np.clip(mastery + gain, 0.0, 1.0))
