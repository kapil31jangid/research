"""Question read endpoints; answers are deliberately excluded from responses."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.question import Question
from app.schemas.question import QuestionRead

router = APIRouter(prefix="/questions", tags=["questions"])


def serialise(question: Question) -> dict[str, object]:
    return {
        "id": question.id,
        "concept_id": question.concept_id,
        "text": question.text,
        "answer_type": question.answer_type,
        "options": json.loads(question.options),
        "difficulty": question.difficulty,
        "explanation": question.explanation,
        "diagnostic_value": question.diagnostic_value,
        "estimated_cost_ms": question.estimated_cost_ms,
        "misconception_patterns": json.loads(question.misconception_patterns),
        "template_id": question.template_id,
    }


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


@router.get("/{question_id}", response_model=QuestionRead)
async def get_question(question_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return serialise(question)
