"""Learner-safe curriculum discovery and pathway schemas."""

from pydantic import BaseModel, Field


class BoardRead(BaseModel):
    id: str
    name: str
    country: str | None
    description: str | None


class ClassOptionRead(BaseModel):
    board_id: str
    class_level: int = Field(ge=1, le=12)
    content_status: str


class SubjectRead(BaseModel):
    id: str
    board_id: str
    class_level: int
    name: str
    slug: str
    description: str
    content_status: str
    is_active: bool
    curriculum_pack_id: str | None
    curriculum_pack_version: str | None


class BookRead(BaseModel):
    id: str
    subject_id: str
    title: str
    source: str
    language: str
    official_reference_url: str | None
    edition: str | None
    is_active: bool


class ChapterRead(BaseModel):
    id: str
    book_id: str
    chapter_number: int
    title: str
    slug: str
    description: str
    sequence: int
    concept_ids: list[str]
    is_active: bool


class CurriculumContextRead(BaseModel):
    board_id: str
    board_name: str
    class_level: int
    subject_id: str
    subject_name: str
    book_id: str
    book_title: str
    chapter_id: str
    chapter_title: str
    concept_id: str | None
    concept_name: str | None
    curriculum_pack_id: str
    curriculum_pack_version: str
    content_origin: str


class LearningPathwayUpdate(BaseModel):
    board_id: str = "ncert"
    class_level: int = Field(ge=1, le=12)
    subject_id: str
    book_id: str | None = None
    chapter_id: str | None = None
