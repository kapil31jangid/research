"""Learner state DTOs and BKT parameter selection."""

from dataclasses import dataclass

from app.learner_model.bkt import BKTParameters

CONCEPT_BKT_OVERRIDES: dict[str, BKTParameters] = {
    "fraction_addition": BKTParameters(
        learning_probability=0.10, slip_probability=0.14, guess_probability=0.16
    ),
    "equivalent_fractions": BKTParameters(
        learning_probability=0.13, slip_probability=0.11, guess_probability=0.18
    ),
}


@dataclass(frozen=True)
class LearnerStateSummary:
    learner_id: str
    concept_id: str
    mastery_probability: float
    retained_mastery: float
    uncertainty: float
    attempts: int


def parameters_for_difficulty(difficulty: int) -> BKTParameters:
    """Provide conservative, deterministic per-difficulty BKT defaults."""
    parameter_sets = {
        1: BKTParameters(learning_probability=0.18, slip_probability=0.08, guess_probability=0.22),
        2: BKTParameters(learning_probability=0.15, slip_probability=0.10, guess_probability=0.20),
        3: BKTParameters(learning_probability=0.12, slip_probability=0.12, guess_probability=0.18),
    }
    return parameter_sets.get(difficulty, BKTParameters())


def parameters_for_concept(concept_id: str, difficulty: int) -> BKTParameters:
    """Return a concept override when available, otherwise its difficulty default."""
    return CONCEPT_BKT_OVERRIDES.get(concept_id, parameters_for_difficulty(difficulty))
