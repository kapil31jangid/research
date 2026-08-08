"""Deterministic synthetic learner population; not real learner data."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SyntheticLearner:
    synthetic_learner_id: str
    profile: str
    latent_skill: float
    initial_mastery_by_concept: dict[str, float]
    response_speed_factor: float
    hint_probability: float
    misconception_tendency: float
    forgetting_factor: float
    resource_profile: str
    offline_probability: float


_PROFILE = {
    "strong": (0.75, 0.1, 0.05, "high_end", 0.02),
    "average": (0.5, 0.2, 0.1, "mid_range", 0.05),
    "struggling": (0.25, 0.3, 0.15, "low_end", 0.1),
    "misconception_heavy": (0.4, 0.2, 0.6, "mid_range", 0.08),
    "slow_responder": (0.5, 0.1, 0.1, "mid_range", 0.05),
    "high_hint_usage": (0.45, 0.7, 0.1, "mid_range", 0.05),
    "forgetful": (0.5, 0.2, 0.1, "mid_range", 0.08),
    "offline_constrained": (0.45, 0.2, 0.1, "offline", 0.7),
    "low_resource": (0.45, 0.2, 0.1, "low_end", 0.2),
    "mixed": (0.5, 0.2, 0.1, "mixed", 0.1),
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
        skill, hints, misconception, resource, offline = _PROFILE[profile]
        learners.append(
            SyntheticLearner(
                f"synthetic_{index:05d}",
                profile,
                float(np.clip(rng.normal(skill, 0.08), 0, 1)),
                {concept: float(np.clip(rng.normal(skill, 0.1), 0, 1)) for concept in concept_ids},
                float(rng.uniform(0.7, 1.8)),
                hints,
                misconception,
                0.08 if profile == "forgetful" else 0.03,
                resource,
                offline,
            )
        )
    return learners
