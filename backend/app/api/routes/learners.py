"""Local learner profile endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.learner import Learner
from app.schemas.learner import LearnerCreate, LearnerRead

router = APIRouter(prefix="/learners", tags=["learners"])


@router.post("", response_model=LearnerRead, status_code=status.HTTP_201_CREATED)
async def create_learner(payload: LearnerCreate, db: Session = Depends(get_db)) -> Learner:
    learner = Learner(**payload.model_dump())
    db.add(learner)
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
