"""Question response schemas."""

from pydantic import BaseModel, Field


class QuestionRead(BaseModel):
    id: str
    concept_id: str
    text: str
    answer_type: str
    options: list[str]
    difficulty: int = Field(ge=1, le=3)
    explanation: str
    diagnostic_value: float = Field(ge=0, le=1)
    estimated_cost_ms: int
    misconception_patterns: list[str]
    template_id: str | None = None
