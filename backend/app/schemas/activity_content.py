"""Typed learner-facing activity content documents."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.schemas.curriculum import CurriculumContextRead


class ExplanationSection(BaseModel):
    type: Literal["explanation"]
    heading: str | None = None
    body: str


class WorkedExampleSection(BaseModel):
    type: Literal["worked_example"]
    heading: str = "Worked example"
    problem: str
    steps: list[str] = Field(min_length=1)
    answer: str
    reasoning: str | None = None


class StepsSection(BaseModel):
    type: Literal["steps"]
    heading: str
    steps: list[str] = Field(min_length=1)


class CalloutSection(BaseModel):
    type: Literal["tip", "warning", "formula", "reflection"]
    heading: str | None = None
    body: str


class FractionVisualSection(BaseModel):
    type: Literal["visual_model", "fraction_bar"]
    heading: str | None = None
    numerator: int = Field(ge=0)
    denominator: int = Field(gt=0, le=24)
    comparison_numerator: int | None = Field(default=None, ge=0)
    comparison_denominator: int | None = Field(default=None, gt=0, le=24)
    caption: str


class NumberLineSection(BaseModel):
    type: Literal["number_line"]
    heading: str | None = None
    denominator: int = Field(gt=0, le=24)
    points: list[int] = Field(default_factory=list)
    caption: str


class CheckpointSection(BaseModel):
    type: Literal["checkpoint", "practice"]
    heading: str = "Quick check"
    prompt: str
    options: list[str] = Field(default_factory=list)
    hint: str | None = None


ActivitySection = Annotated[
    ExplanationSection
    | WorkedExampleSection
    | StepsSection
    | CalloutSection
    | FractionVisualSection
    | NumberLineSection
    | CheckpointSection,
    Field(discriminator="type"),
]


class ActivityContent(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    concept_id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=160)
    subtitle: str | None = Field(default=None, max_length=240)
    content_type: str = Field(min_length=1, max_length=40)
    estimated_minutes: int | None = Field(default=None, ge=1, le=60)
    learning_objective: str | None = Field(default=None, max_length=400)
    sections: list[ActivitySection] = Field(min_length=1)
    offline_ready: bool = True
    content_origin: Literal["original_adaptive_material"] = "original_adaptive_material"
    aligned_board: str = "NCERT"
    official_reference_url: str | None = None


class ActivitySummaryRead(BaseModel):
    id: str
    concept_id: str
    title: str
    activity_type: str
    difficulty: float
    available_offline: bool
    estimated_minutes: int | None = None
    curriculum_context: CurriculumContextRead


class ActivityContentRead(BaseModel):
    activity: ActivitySummaryRead
    content: ActivityContent
