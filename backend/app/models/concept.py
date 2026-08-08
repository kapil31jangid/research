"""Curriculum concept persistence model."""

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    chapter_id: Mapped[str] = mapped_column(
        ForeignKey("curriculum_chapters.id"),
        index=True,
        default="ncert-c5-math-fractions",
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    mastery_threshold: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    prerequisite_ids: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    activity_ids: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    misconception_ids: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
