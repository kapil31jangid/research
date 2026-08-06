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
    requested_adaptation_path: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    fallback_used: Mapped[bool] = mapped_column(default=False, nullable=False)
    fallback_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ml_model_available: Mapped[bool] = mapped_column(default=False, nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    predicted_correctness_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    triggered_rules: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    rejected_paths: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    offline_content_available: Mapped[bool] = mapped_column(default=False, nullable=False)
    matching_offline_activity_ids: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    expected_learning_gain: Mapped[float] = mapped_column(Float, nullable=False)
    computational_cost_ms: Mapped[float] = mapped_column(Float, nullable=False)
    measured_controller_latency_ms: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    measured_recommendation_latency_ms: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    measured_total_adaptive_latency_ms: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    controller_mode: Mapped[str] = mapped_column(
        String(60), default="deterministic", nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    alternatives: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    resource_state: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
