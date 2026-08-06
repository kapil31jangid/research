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
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
