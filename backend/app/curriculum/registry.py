"""Validated, immutable NCERT-aligned curriculum metadata registry."""

import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl, model_validator

CONTENT_STATUSES = {"available", "partial", "planned"}
CONTENT_ORIGIN = "original_adaptive_material"
REGISTRY_PATH = Path(__file__).resolve().parents[3] / "data/curriculum/ncert/registry.json"


class BoardDefinition(BaseModel):
    id: str
    name: str
    country: str | None = None
    description: str | None = None


class ClassDefinition(BaseModel):
    board_id: str
    class_level: int = Field(ge=1, le=12)
    content_status: str


class SubjectDefinition(BaseModel):
    id: str
    board_id: str
    class_level: int = Field(ge=1, le=12)
    name: str
    slug: str
    description: str = ""
    content_status: str
    is_active: bool = True
    curriculum_pack_id: str | None = None
    curriculum_pack_version: str | None = None


class BookDefinition(BaseModel):
    id: str
    subject_id: str
    title: str
    source: str
    language: str = "English"
    official_reference_url: HttpUrl | None = None
    edition: str | None = None
    is_active: bool = True


class ChapterDefinition(BaseModel):
    id: str
    book_id: str
    chapter_number: int = Field(ge=1)
    title: str
    slug: str
    description: str = ""
    sequence: int = Field(ge=1)
    concept_ids: list[str] = Field(default_factory=list)
    is_active: bool = True


class CurriculumRegistryDocument(BaseModel):
    boards: list[BoardDefinition]
    classes: list[ClassDefinition]
    subjects: list[SubjectDefinition]
    books: list[BookDefinition]
    chapters: list[ChapterDefinition]

    @model_validator(mode="after")
    def validate_relationships(self) -> "CurriculumRegistryDocument":
        _require_unique("board", [item.id for item in self.boards])
        _require_unique("class", [f"{item.board_id}:{item.class_level}" for item in self.classes])
        _require_unique("subject", [item.id for item in self.subjects])
        _require_unique("book", [item.id for item in self.books])
        _require_unique("chapter", [item.id for item in self.chapters])
        board_ids = {item.id for item in self.boards}
        subject_ids = {item.id for item in self.subjects}
        book_ids = {item.id for item in self.books}
        for item in self.classes:
            if item.board_id not in board_ids:
                raise ValueError(f"Class {item.class_level} references unknown board")
            _require_status(item.content_status)
        for item in self.subjects:
            if item.board_id not in board_ids:
                raise ValueError(f"Subject {item.id} references unknown board")
            if not any(
                level.board_id == item.board_id and level.class_level == item.class_level
                for level in self.classes
            ):
                raise ValueError(f"Subject {item.id} references unknown class")
            _require_status(item.content_status)
        for item in self.books:
            if item.subject_id not in subject_ids:
                raise ValueError(f"Book {item.id} references unknown subject")
        chapter_sequences: set[tuple[str, int]] = set()
        for item in self.chapters:
            if item.book_id not in book_ids:
                raise ValueError(f"Chapter {item.id} references unknown book")
            key = (item.book_id, item.sequence)
            if key in chapter_sequences:
                raise ValueError(f"Duplicate chapter sequence {key}")
            chapter_sequences.add(key)
        return self


class CurriculumContext(BaseModel):
    board_id: str
    board_name: str
    class_level: int
    subject_id: str
    subject_name: str
    book_id: str
    book_title: str
    chapter_id: str
    chapter_title: str
    concept_id: str | None = None
    concept_name: str | None = None
    curriculum_pack_id: str
    curriculum_pack_version: str
    content_origin: str = CONTENT_ORIGIN


class ContentPackManifest(BaseModel):
    id: str
    board: str
    class_level: int = Field(ge=1, le=12)
    subject: str
    version: str
    language: str
    content_origin: str
    aligned_source: str
    official_reference_url: HttpUrl
    chapter_ids: list[str] = Field(min_length=1)


def _require_unique(kind: str, identifiers: list[str]) -> None:
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"Duplicate {kind} identifiers")


def _require_status(status: str) -> None:
    if status not in CONTENT_STATUSES:
        raise ValueError(f"Unsupported content status: {status}")


@lru_cache(maxsize=1)
def load_curriculum_registry() -> CurriculumRegistryDocument:
    with REGISTRY_PATH.open(encoding="utf-8") as source:
        return CurriculumRegistryDocument.model_validate(json.load(source))


def get_boards() -> tuple[BoardDefinition, ...]:
    return tuple(load_curriculum_registry().boards)


def get_classes(board_id: str) -> tuple[ClassDefinition, ...]:
    return tuple(item for item in load_curriculum_registry().classes if item.board_id == board_id)


def get_subjects(board_id: str, class_level: int) -> tuple[SubjectDefinition, ...]:
    return tuple(
        item
        for item in load_curriculum_registry().subjects
        if item.board_id == board_id and item.class_level == class_level
    )


def get_books(subject_id: str) -> tuple[BookDefinition, ...]:
    return tuple(item for item in load_curriculum_registry().books if item.subject_id == subject_id)


def get_chapters(book_id: str) -> tuple[ChapterDefinition, ...]:
    return tuple(
        sorted(
            (item for item in load_curriculum_registry().chapters if item.book_id == book_id),
            key=lambda item: item.sequence,
        )
    )


def concept_ids_for_subject(subject_id: str) -> set[str]:
    book_ids = {item.id for item in get_books(subject_id) if item.is_active}
    return {
        concept_id
        for chapter in load_curriculum_registry().chapters
        if chapter.book_id in book_ids and chapter.is_active
        for concept_id in chapter.concept_ids
    }


def concept_ids_for_chapter(chapter_id: str) -> set[str]:
    chapter = next(
        (item for item in load_curriculum_registry().chapters if item.id == chapter_id), None
    )
    return set(chapter.concept_ids) if chapter and chapter.is_active else set()


def chapter_for_concept(concept_id: str) -> ChapterDefinition | None:
    return next(
        (
            chapter
            for chapter in load_curriculum_registry().chapters
            if concept_id in chapter.concept_ids
        ),
        None,
    )


def get_curriculum_context(concept_id: str, concept_name: str | None = None) -> CurriculumContext:
    registry = load_curriculum_registry()
    chapter = chapter_for_concept(concept_id)
    if chapter is None:
        raise KeyError(f"Concept {concept_id} has no curriculum chapter")
    book = next(item for item in registry.books if item.id == chapter.book_id)
    subject = next(item for item in registry.subjects if item.id == book.subject_id)
    board = next(item for item in registry.boards if item.id == subject.board_id)
    if not subject.curriculum_pack_id or not subject.curriculum_pack_version:
        raise ValueError(f"Subject {subject.id} has no versioned content pack")
    return CurriculumContext(
        board_id=board.id,
        board_name=board.name,
        class_level=subject.class_level,
        subject_id=subject.id,
        subject_name=subject.name,
        book_id=book.id,
        book_title=book.title,
        chapter_id=chapter.id,
        chapter_title=chapter.title,
        concept_id=concept_id,
        concept_name=concept_name,
        curriculum_pack_id=subject.curriculum_pack_id,
        curriculum_pack_version=subject.curriculum_pack_version,
    )


def resolve_available_pathway(
    board_id: str,
    class_level: int,
    subject_id: str,
    book_id: str | None = None,
    chapter_id: str | None = None,
) -> tuple[SubjectDefinition, BookDefinition, ChapterDefinition]:
    subject = next(
        (
            item
            for item in get_subjects(board_id, class_level)
            if item.id == subject_id and item.is_active
        ),
        None,
    )
    if subject is None or subject.content_status != "available":
        raise ValueError("This learning pathway is not available yet")
    books = tuple(item for item in get_books(subject.id) if item.is_active)
    book = next((item for item in books if item.id == book_id), None) if book_id else None
    if book is None and books:
        book = books[0]
    if book is None:
        raise ValueError("This subject has no active book")
    chapters = tuple(item for item in get_chapters(book.id) if item.is_active)
    chapter = (
        next((item for item in chapters if item.id == chapter_id), None) if chapter_id else None
    )
    if chapter is None and chapters:
        chapter = chapters[0]
    if chapter is None:
        raise ValueError("This subject has no active chapter")
    return subject, book, chapter


def clear_curriculum_registry_cache() -> None:
    load_curriculum_registry.cache_clear()


def load_content_pack_manifests() -> tuple[ContentPackManifest, ...]:
    manifests: list[ContentPackManifest] = []
    for path in sorted(REGISTRY_PATH.parent.rglob("manifest.json")):
        with path.open(encoding="utf-8") as source:
            manifests.append(ContentPackManifest.model_validate(json.load(source)))
    return tuple(manifests)


def validate_curriculum_registry(
    *,
    concepts: list[dict[str, object]],
    activities: list[dict[str, object]],
    questions: list[dict[str, object]],
) -> None:
    """Fail fast when hierarchy, packs, and adaptive seed references diverge."""
    registry = load_curriculum_registry()
    concept_ids = [str(item["id"]) for item in concepts]
    _require_unique("concept", concept_ids)
    concept_id_set = set(concept_ids)
    chapter_concepts = [concept_id for item in registry.chapters for concept_id in item.concept_ids]
    _require_unique("chapter concept", chapter_concepts)
    if set(chapter_concepts) != concept_id_set:
        missing = concept_id_set - set(chapter_concepts)
        unknown = set(chapter_concepts) - concept_id_set
        raise ValueError(
            "Curriculum chapter mapping mismatch; "
            f"missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    chapter_ids = {item.id for item in registry.chapters}
    for concept in concepts:
        if concept.get("chapter_id") not in chapter_ids:
            raise ValueError(f"Concept {concept['id']} references an unknown chapter")
        for prerequisite in concept.get("prerequisite_ids", []):
            if prerequisite not in concept_id_set:
                raise ValueError(f"Concept {concept['id']} has unknown prerequisite {prerequisite}")
    for kind, records in (("activity", activities), ("question", questions)):
        identifiers = [str(item["id"]) for item in records]
        _require_unique(kind, identifiers)
        for item in records:
            if item.get("concept_id") not in concept_id_set:
                raise ValueError(f"{kind.title()} {item['id']} references an unknown concept")
    manifests = load_content_pack_manifests()
    manifest_by_id = {item.id: item for item in manifests}
    _require_unique("content pack", list(manifest_by_id))
    for subject in registry.subjects:
        if subject.content_status != "available":
            continue
        manifest = manifest_by_id.get(subject.curriculum_pack_id or "")
        if manifest is None:
            raise ValueError(f"Available subject {subject.id} has no content-pack manifest")
        if manifest.content_origin != CONTENT_ORIGIN:
            raise ValueError(f"Pack {manifest.id} is not identified as original material")
        if set(manifest.chapter_ids) - chapter_ids:
            raise ValueError(f"Pack {manifest.id} references an unknown chapter")
