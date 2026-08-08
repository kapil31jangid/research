"""Persisted curriculum hierarchy used for scoped adaptive queries."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CurriculumBoard(Base):
    __tablename__ = "curriculum_boards"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class CurriculumSubject(Base):
    __tablename__ = "curriculum_subjects"
    __table_args__ = (
        UniqueConstraint("board_id", "class_level", "slug", name="uq_curriculum_subject"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    board_id: Mapped[str] = mapped_column(ForeignKey("curriculum_boards.id"), index=True)
    class_level: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    content_status: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    curriculum_pack_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    curriculum_pack_version: Mapped[str | None] = mapped_column(String(30), nullable=True)


class CurriculumBook(Base):
    __tablename__ = "curriculum_books"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("curriculum_subjects.id"), index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    language: Mapped[str] = mapped_column(String(40), default="English", nullable=False)
    official_reference_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    edition: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CurriculumChapter(Base):
    __tablename__ = "curriculum_chapters"
    __table_args__ = (
        UniqueConstraint("book_id", "sequence", name="uq_curriculum_chapter_sequence"),
    )

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("curriculum_books.id"), index=True)
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
