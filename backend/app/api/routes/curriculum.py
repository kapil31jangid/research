"""Lightweight curriculum metadata discovery endpoints."""

from fastapi import APIRouter, HTTPException

from app.curriculum.registry import (
    get_boards,
    get_books,
    get_chapters,
    get_classes,
    get_subjects,
    load_curriculum_registry,
)
from app.schemas.curriculum import (
    BoardRead,
    BookRead,
    ChapterRead,
    ClassOptionRead,
    SubjectRead,
)

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


@router.get("/boards", response_model=list[BoardRead])
async def boards() -> list[BoardRead]:
    return [BoardRead.model_validate(item.model_dump()) for item in get_boards()]


@router.get("/boards/{board_id}/classes", response_model=list[ClassOptionRead])
async def classes(board_id: str) -> list[ClassOptionRead]:
    items = get_classes(board_id)
    if not items:
        raise HTTPException(status_code=404, detail="Curriculum board not found")
    return [ClassOptionRead.model_validate(item.model_dump()) for item in items]


@router.get("/boards/{board_id}/classes/{class_level}/subjects", response_model=list[SubjectRead])
async def subjects(board_id: str, class_level: int) -> list[SubjectRead]:
    return [
        SubjectRead.model_validate(item.model_dump())
        for item in get_subjects(board_id, class_level)
    ]


@router.get("/subjects/{subject_id}/books", response_model=list[BookRead])
async def books(subject_id: str) -> list[BookRead]:
    return [BookRead.model_validate(item.model_dump(mode="json")) for item in get_books(subject_id)]


@router.get("/books/{book_id}/chapters", response_model=list[ChapterRead])
async def chapters(book_id: str) -> list[ChapterRead]:
    return [ChapterRead.model_validate(item.model_dump()) for item in get_chapters(book_id)]


@router.get("/chapters/{chapter_id}/concepts", response_model=list[str])
async def chapter_concepts(chapter_id: str) -> list[str]:
    chapter = next(
        (item for item in load_curriculum_registry().chapters if item.id == chapter_id), None
    )
    if chapter is None:
        raise HTTPException(status_code=404, detail="Curriculum chapter not found")
    return chapter.concept_ids
