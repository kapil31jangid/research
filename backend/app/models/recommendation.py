"""Persisted explainable recommendation decisions."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id"), index=True)
    selected_concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    selected_activity_id: Mapped[str] = mapped_column(String(120), nullable=False)
    adaptation_path: Mapped[str] = mapped_column(String(60), nullable=False)
    expected_learning_gain: Mapped[float] = mapped_column(Float, nullable=False)
    computational_cost_ms: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    alternatives: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    resource_state: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
