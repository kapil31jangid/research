"""Local learner profile endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum.registry import resolve_available_pathway
from app.database.session import get_db
from app.models.learner import Learner
from app.schemas.curriculum import LearningPathwayUpdate
from app.schemas.learner import LearnerCreate, LearnerRead
from app.schemas.learning import LearningPlanRead
from app.schemas.state import LearnerConceptStateRead, LearnerProgressRead
from app.services.learner_service import ensure_learner_states, learner_progress, serialise_state
from app.services.learning_service import learning_plan

router = APIRouter(prefix="/learners", tags=["learners"])


@router.post("", response_model=LearnerRead, status_code=status.HTTP_201_CREATED)
async def create_learner(payload: LearnerCreate, db: Session = Depends(get_db)) -> Learner:
    values = payload.model_dump()
    class_level = values.pop("class_level") or payload.grade
    subject_id = values.get("active_subject_id")
    if subject_id is None and class_level in {5, 6}:
        subject_id = f"ncert-c{class_level}-mathematics"
    if subject_id:
        try:
            subject, book, chapter = resolve_available_pathway(
                payload.board_id,
                class_level,
                subject_id,
                values.get("active_book_id"),
                values.get("active_chapter_id"),
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        values.update(
            active_subject_id=subject.id,
            active_book_id=book.id,
            active_chapter_id=chapter.id,
        )
    learner = Learner(**values, class_level=class_level)
    db.add(learner)
    db.commit()
    db.refresh(learner)
    return learner


@router.patch("/{learner_id}/pathway", response_model=LearnerRead)
async def update_pathway(
    learner_id: str,
    payload: LearningPathwayUpdate,
    db: Session = Depends(get_db),
) -> Learner:
    learner = db.get(Learner, learner_id)
    if learner is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    try:
        subject, book, chapter = resolve_available_pathway(
            payload.board_id,
            payload.class_level,
            payload.subject_id,
            payload.book_id,
            payload.chapter_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    learner.board_id = payload.board_id
    learner.class_level = payload.class_level
    learner.active_subject_id = subject.id
    learner.active_book_id = book.id
    learner.active_chapter_id = chapter.id
    db.commit()
    db.refresh(learner)
    return learner


@router.get("", response_model=list[LearnerRead])
async def list_learners(db: Session = Depends(get_db)) -> list[Learner]:
    return list(db.scalars(select(Learner).order_by(Learner.created_at.desc())))


@router.get("/{learner_id}", response_model=LearnerRead)
async def get_learner(learner_id: str, db: Session = Depends(get_db)) -> Learner:
    learner = db.get(Learner, learner_id)
    if learner is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    learner.last_active_at = datetime.now(UTC)
    db.commit()
    db.refresh(learner)
    return learner


@router.get("/{learner_id}/state", response_model=list[LearnerConceptStateRead])
async def get_learner_state(
    learner_id: str, db: Session = Depends(get_db)
) -> list[LearnerConceptStateRead]:
    if db.get(Learner, learner_id) is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return [serialise_state(state) for state in ensure_learner_states(learner_id, db)]


@router.get("/{learner_id}/progress", response_model=LearnerProgressRead)
async def get_learner_progress(
    learner_id: str, db: Session = Depends(get_db)
) -> LearnerProgressRead:
    if db.get(Learner, learner_id) is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return learner_progress(learner_id, db)


@router.get("/{learner_id}/learning-plan", response_model=LearningPlanRead)
async def get_learning_plan(learner_id: str, db: Session = Depends(get_db)) -> LearningPlanRead:
    if db.get(Learner, learner_id) is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return learning_plan(learner_id, db)
