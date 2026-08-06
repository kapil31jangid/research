"""Interaction request and complete adaptive-loop response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.recommendations import RecommendationRead
from app.schemas.resources import ResourceSimulationRequest, ResourceStateRead
from app.schemas.state import LearnerConceptStateRead


class InteractionCreate(BaseModel):
    learner_id: str
    question_id: str
    submitted_answer: str = Field(min_length=1, max_length=500)
    response_time_ms: int = Field(ge=0, le=3_600_000)
    hints_used: int = Field(default=0, ge=0, le=20)
    offline: bool = False
    device_resource_state: ResourceSimulationRequest | None = None


class InteractionRead(BaseModel):
    id: str
    learner_id: str
    question_id: str
    concept_id: str
    submitted_answer: str
    correct: bool
    response_time_ms: int
    hints_used: int
    offline: bool
    created_at: datetime


class MisconceptionRead(BaseModel):
    detected: bool
    id: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str | None = None
    remediation_activity: str | None = None


class AdaptiveInteractionResponse(BaseModel):
    learner_id: str
    interaction_result: InteractionRead
    learner_state: LearnerConceptStateRead
    misconception: MisconceptionRead
    resource_state: ResourceStateRead
    decision: RecommendationRead
    explanation: list[str]
