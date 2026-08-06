"""Learner concept-state API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class LearnerConceptStateRead(BaseModel):
    concept_id: str
    mastery_probability: float = Field(ge=0.0, le=1.0)
    retained_mastery: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    attempts: int = Field(ge=0)
    correct_attempts: int = Field(ge=0)
    recent_correctness: list[bool]
    average_response_time: float | None
    response_time_variation: float = Field(ge=0.0, le=1.0)
    hint_usage_rate: float = Field(ge=0.0, le=1.0)
    last_practised_at: datetime | None
    forgetting_rate: float = Field(ge=0.0)
    suspected_misconception: str | None
    misconception_confidence: float = Field(ge=0.0, le=1.0)


class LearnerProgressRead(BaseModel):
    learner_id: str
    concept_count: int
    average_mastery: float = Field(ge=0.0, le=1.0)
    average_retained_mastery: float = Field(ge=0.0, le=1.0)
    average_uncertainty: float = Field(ge=0.0, le=1.0)
    total_attempts: int = Field(ge=0)
    states: list[LearnerConceptStateRead]
