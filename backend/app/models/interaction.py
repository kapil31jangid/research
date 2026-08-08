"""Learner answer events retained for modelling and misconception evidence."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    submitted_answer: Mapped[str] = mapped_column(Text, nullable=False)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    hints_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    resource_state: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    offline: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    board_id: Mapped[str] = mapped_column(String(40), default="ncert", nullable=False)
    class_level: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    subject_id: Mapped[str] = mapped_column(String(100), default="ncert-c5-mathematics")
    book_id: Mapped[str] = mapped_column(String(120), default="ncert-c5-math-reference")
    chapter_id: Mapped[str] = mapped_column(String(120), default="ncert-c5-math-fractions")
    curriculum_pack_version: Mapped[str] = mapped_column(String(30), default="1.0.0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
