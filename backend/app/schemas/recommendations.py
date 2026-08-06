"""Recommendation API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class RecommendationAlternativeRead(BaseModel):
    concept_id: str
    activity_id: str
    score: float
    explanation: str


class RecommendationRead(BaseModel):
    id: str
    learner_id: str
    selected_concept_id: str
    selected_activity_id: str
    adaptation_path: str
    expected_learning_gain: float = Field(ge=0.0, le=1.0)
    computational_cost_ms: float = Field(ge=0.0)
    score: float
    explanation: list[str]
    alternatives: list[RecommendationAlternativeRead]
    created_at: datetime


class GenerateRecommendationRequest(BaseModel):
    learner_id: str
    concept_id: str | None = None
