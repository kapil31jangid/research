"""Persisted learner submission endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.learner import Learner
from app.models.question import Question
from app.schemas.interactions import AdaptiveInteractionResponse, InteractionCreate
from app.services.interaction_service import process_interaction

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("", response_model=AdaptiveInteractionResponse, status_code=status.HTTP_201_CREATED)
async def submit_interaction(
    payload: InteractionCreate, db: Session = Depends(get_db)
) -> AdaptiveInteractionResponse:
    if db.get(Learner, payload.learner_id) is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    question = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    interaction, learner_state, misconception, resource, recommendation = process_interaction(
        payload, question, db
    )
    return AdaptiveInteractionResponse(
        learner_id=payload.learner_id,
        interaction_result=interaction,
        learner_state=learner_state,
        misconception=misconception,
        resource_state=resource,
        decision=recommendation,
        explanation=recommendation.explanation,
    )


@router.get("/{learner_id}")
async def learner_interactions(
    learner_id: str, db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    from app.models.interaction import Interaction

    return [
        {
            "id": item.id,
            "question_id": item.question_id,
            "concept_id": item.concept_id,
            "correct": item.correct,
            "response_time_ms": item.response_time_ms,
            "offline": item.offline,
            "created_at": item.created_at,
        }
        for item in db.scalars(
            select(Interaction)
            .where(Interaction.learner_id == learner_id)
            .order_by(Interaction.created_at.desc())
        )
    ]
