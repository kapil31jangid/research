"""Question read endpoints; answers are deliberately excluded from responses."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.learner import Learner
from app.models.question import Question
from app.schemas.learning import LearningSelectionRead
from app.schemas.question import QuestionRead
from app.services.learning_service import select_next_question
from app.services.question_service import serialise_question

router = APIRouter(prefix="/questions", tags=["questions"])


def serialise(question: Question) -> dict[str, object]:
    return serialise_question(question)


@router.get("", response_model=list[QuestionRead])
async def list_questions(
    concept_id: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    query = select(Question).order_by(Question.id).limit(limit)
    if concept_id:
        query = (
            select(Question)
            .where(Question.concept_id == concept_id)
            .order_by(Question.id)
            .limit(limit)
        )
    return [serialise(question) for question in db.scalars(query)]


@router.get("/next", response_model=LearningSelectionRead)
async def next_question(learner_id: str, db: Session = Depends(get_db)) -> LearningSelectionRead:
    if db.get(Learner, learner_id) is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    selection = select_next_question(learner_id, db)
    if selection is None:
        raise HTTPException(status_code=404, detail="No eligible question available")
    return selection


@router.get("/{question_id}", response_model=QuestionRead)
async def get_question(question_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return serialise(question)
