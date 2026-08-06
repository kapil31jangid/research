"""Numerically safe Bayesian Knowledge Tracing updates."""

from pydantic import BaseModel, Field, model_validator


class BKTParameters(BaseModel):
    """Per-concept BKT parameters, validated as probabilities."""

    initial_mastery: float = Field(default=0.2, ge=0.0, le=1.0)
    learning_probability: float = Field(default=0.15, ge=0.0, le=1.0)
    slip_probability: float = Field(default=0.1, ge=0.0, le=1.0)
    guess_probability: float = Field(default=0.2, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_observation_model(self) -> "BKTParameters":
        if self.slip_probability == 1.0 and self.guess_probability == 0.0:
            raise ValueError("Slip=1 and guess=0 make correct-response evidence undefined")
        return self


def clamp_probability(value: float) -> float:
    """Clamp a numerical result to the closed probability interval."""
    return max(0.0, min(1.0, value))


def update_mastery(mastery: float, correct: bool, parameters: BKTParameters) -> float:
    """Apply one BKT observation and learning transition."""
    mastery = clamp_probability(mastery)
    if correct:
        numerator = mastery * (1.0 - parameters.slip_probability)
        denominator = numerator + (1.0 - mastery) * parameters.guess_probability
    else:
        numerator = mastery * parameters.slip_probability
        denominator = numerator + (1.0 - mastery) * (1.0 - parameters.guess_probability)
    posterior = mastery if denominator <= 1e-12 else numerator / denominator
    return clamp_probability(posterior + (1.0 - posterior) * parameters.learning_probability)
