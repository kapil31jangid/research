"""Learner request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LearnerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age_group: str = Field(min_length=1, max_length=40)
    grade: int = Field(ge=1, le=12)
    preferred_language: str = Field(default="en", min_length=2, max_length=12)
    device_profile: str = Field(default="unknown", max_length=40)
    board_id: str = "ncert"
    class_level: int | None = Field(default=None, ge=1, le=12)
    active_subject_id: str | None = None
    active_book_id: str | None = None
    active_chapter_id: str | None = None


class LearnerRead(LearnerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    last_active_at: datetime
