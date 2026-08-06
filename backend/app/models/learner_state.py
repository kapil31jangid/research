"""Persisted learner knowledge estimates and their evaluation history."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class LearnerConceptState(Base):
    """Current, mutable estimate for one learner and curriculum concept."""

    __tablename__ = "learner_concept_states"
    __table_args__ = (
        UniqueConstraint("learner_id", "concept_id", name="uq_learner_concept_state"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id"), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    mastery_probability: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    uncertainty: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recent_correctness: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    average_response_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    response_time_variation: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hint_usage_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_practised_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    forgetting_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    suspected_misconception: Mapped[str | None] = mapped_column(String(80), nullable=True)
    misconception_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)


class MasteryHistory(Base):
    """Append-only mastery observations used for research evaluation."""

    __tablename__ = "mastery_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id"), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    mastery_probability: Mapped[float] = mapped_column(Float, nullable=False)
    uncertainty: Mapped[float] = mapped_column(Float, nullable=False)
    observed_correctness: Mapped[bool | None] = mapped_column(nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
