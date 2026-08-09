"""Deterministic synthetic learner population; not real learner data."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SyntheticLearner:
    synthetic_learner_id: str
    profile: str
    latent_skill: float
    initial_mastery_by_concept: dict[str, float]
    learning_rate: float
    guess_probability: float
    slip_probability: float
    response_speed_factor: float
    hint_probability: float
    misconception_tendency: float
    forgetting_factor: float
    interruption_probability: float
    resource_profile: str
    offline_probability: float


@dataclass(frozen=True)
class SyntheticProfile:
    initial_mastery: float
    learning_rate: float
    guess_probability: float
    slip_probability: float
    response_speed_factor: float
    hint_probability: float
    misconception_tendency: float
    forgetting_rate: float
    interruption_probability: float
    resource_profile: str
    offline_probability: float


# These are explicit heuristic simulation assumptions, not estimates from learners.
PROFILES: dict[str, SyntheticProfile] = {
    "fast_learner": SyntheticProfile(
        0.65, 0.10, 0.08, 0.05, 0.80, 0.10, 0.08, 0.02, 0.03, "high_end", 0.02
    ),
    "slow_learner": SyntheticProfile(
        0.30, 0.04, 0.08, 0.12, 1.45, 0.25, 0.12, 0.04, 0.08, "mid_range", 0.05
    ),
    "elevated_guess": SyntheticProfile(
        0.35, 0.07, 0.28, 0.08, 1.00, 0.15, 0.10, 0.03, 0.05, "mid_range", 0.05
    ),
    "elevated_slip": SyntheticProfile(
        0.50, 0.07, 0.05, 0.25, 1.00, 0.15, 0.10, 0.03, 0.05, "mid_range", 0.05
    ),
    "stronger_forgetting": SyntheticProfile(
        0.50, 0.07, 0.08, 0.10, 1.00, 0.20, 0.10, 0.12, 0.12, "mid_range", 0.08
    ),
    "misconception_prone": SyntheticProfile(
        0.40, 0.06, 0.08, 0.12, 1.00, 0.20, 0.55, 0.04, 0.08, "mid_range", 0.08
    ),
    "intermittent": SyntheticProfile(
        0.45, 0.06, 0.08, 0.10, 1.10, 0.20, 0.12, 0.06, 0.45, "mixed", 0.25
    ),
    "constrained_resource": SyntheticProfile(
        0.45, 0.06, 0.08, 0.12, 1.10, 0.25, 0.12, 0.05, 0.15, "low_end", 0.35
    ),
    # Compatibility profiles retained for small existing fixtures.
    "strong": SyntheticProfile(
        0.75, 0.10, 0.05, 0.05, 0.80, 0.10, 0.05, 0.02, 0.03, "high_end", 0.02
    ),
    "struggling": SyntheticProfile(
        0.25, 0.04, 0.08, 0.15, 1.30, 0.30, 0.15, 0.05, 0.10, "low_end", 0.10
    ),
    "misconception_heavy": SyntheticProfile(
        0.40, 0.06, 0.08, 0.12, 1.00, 0.20, 0.60, 0.04, 0.08, "mid_range", 0.08
    ),
    "mixed": SyntheticProfile(0.50, 0.07, 0.08, 0.10, 1.00, 0.20, 0.10, 0.03, 0.08, "mixed", 0.10),
}


def generate_learners(
    count: int, concept_ids: list[str], seed: int, distribution: dict[str, float]
) -> list[SyntheticLearner]:
    rng = np.random.default_rng(seed)
    profiles = list(distribution)
    values = np.array([distribution[item] for item in profiles], dtype=float)
    selected = rng.choice(profiles, size=count, p=values / values.sum())
    learners = []
    for index, profile in enumerate(selected):
        parameters = PROFILES[profile]
        learners.append(
            SyntheticLearner(
                f"synthetic_{index:05d}",
                profile,
                float(np.clip(rng.normal(parameters.initial_mastery, 0.08), 0, 1)),
                {
                    concept: float(np.clip(rng.normal(parameters.initial_mastery, 0.1), 0, 1))
                    for concept in concept_ids
                },
                parameters.learning_rate,
                parameters.guess_probability,
                parameters.slip_probability,
                parameters.response_speed_factor,
                parameters.hint_probability,
                parameters.misconception_tendency,
                parameters.forgetting_rate,
                parameters.interruption_probability,
                parameters.resource_profile,
                parameters.offline_probability,
            )
        )
    return learners
