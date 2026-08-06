"""Schemas for diagnostic and revision activity selection."""

from pydantic import BaseModel, Field

from app.schemas.question import QuestionRead


class LearningSelectionRead(BaseModel):
    learner_id: str
    selection_type: str
    concept_id: str
    question: QuestionRead
    rationale: str
    prerequisite_mastery: float = Field(ge=0.0, le=1.0)


class LearningPlanRead(BaseModel):
    learner_id: str
    ready_concept_ids: list[str]
    revision_concept_ids: list[str]
    blocked_concept_ids: list[str]
