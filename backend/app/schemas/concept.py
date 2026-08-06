"""Concept response schemas."""

from pydantic import BaseModel, ConfigDict, Field


class ConceptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str
    difficulty: int = Field(ge=1, le=3)
    mastery_threshold: float = Field(ge=0, le=1)
    prerequisite_ids: list[str]
    activity_ids: list[str]
    misconception_ids: list[str]
