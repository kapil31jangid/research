"""Learner persistence model."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Learner(Base):
    __tablename__ = "learners"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age_group: Mapped[str] = mapped_column(String(40), nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(12), default="en", nullable=False)
    device_profile: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)
    board_id: Mapped[str] = mapped_column(String(40), default="ncert", nullable=False)
    class_level: Mapped[int] = mapped_column(Integer, default=5, nullable=False, index=True)
    active_subject_id: Mapped[str | None] = mapped_column(
        String(100), default="ncert-c5-mathematics", nullable=True, index=True
    )
    active_book_id: Mapped[str | None] = mapped_column(
        String(120), default="ncert-c5-math-reference", nullable=True
    )
    active_chapter_id: Mapped[str | None] = mapped_column(
        String(120), default="ncert-c5-math-fractions", nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
