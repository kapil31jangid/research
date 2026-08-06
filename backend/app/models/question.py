"""Diagnostic and practice question persistence model."""

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    concept_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_type: Mapped[str] = mapped_column(String(30), default="multiple_choice", nullable=False)
    options: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(120), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    diagnostic_value: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    estimated_cost_ms: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    misconception_patterns: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    template_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
