"""Explicit adaptive learning activity metadata."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class LearningActivity(Base):
    __tablename__ = "learning_activities"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    activity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    available_offline: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    bundled_locally: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    adaptation_paths: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    misconception_ids: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    local_asset_key: Mapped[str | None] = mapped_column(String(160), nullable=True)
    content_type: Mapped[str] = mapped_column(String(40), default="lesson", nullable=False)
    estimated_size_kb: Mapped[int] = mapped_column(Integer, default=64, nullable=False)
    estimated_computational_cost_ms: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False
    )
    content_origin: Mapped[str] = mapped_column(
        String(50), default="original_adaptive_material", nullable=False
    )
    aligned_board: Mapped[str] = mapped_column(String(40), default="ncert", nullable=False)
    official_reference_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    curriculum_pack_id: Mapped[str] = mapped_column(String(120), nullable=False)
    curriculum_pack_version: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deprecation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
