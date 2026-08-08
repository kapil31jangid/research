"""Persisted learner submission endpoint."""

import networkx as nx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum.graph import build_graph
from app.curriculum.loader import load_concepts
from app.curriculum.registry import get_curriculum_context
from app.database.session import get_db
from app.models.learner import Learner
from app.models.question import Question
from app.schemas.interactions import AdaptiveInteractionResponse, InteractionCreate
from app.services.interaction_service import process_interaction
from app.services.learner_service import active_concept_ids

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
    context = get_curriculum_context(question.concept_id)
    if payload.curriculum_context is not None:
        supplied = payload.curriculum_context
        expected = (
            context.board_id,
            context.class_level,
            context.subject_id,
            context.book_id,
            context.chapter_id,
            context.curriculum_pack_version,
        )
        actual = (
            supplied.board_id,
            supplied.class_level,
            supplied.subject_id,
            supplied.book_id,
            supplied.chapter_id,
            supplied.curriculum_pack_version,
        )
        if actual != expected:
            raise HTTPException(status_code=422, detail="Interaction curriculum context mismatch")
    else:
        active_ids = active_concept_ids(payload.learner_id, db)
        graph = build_graph(load_concepts())
        permitted = set(active_ids)
        for concept_id in active_ids:
            permitted.update(nx.ancestors(graph, concept_id))
        if question.concept_id not in permitted:
            raise HTTPException(status_code=422, detail="Question is outside the active pathway")
    result = process_interaction(payload, question, db)
    return AdaptiveInteractionResponse(
        learner_id=payload.learner_id,
        interaction_result=result.interaction,
        learner_state=result.learner_state,
        misconception=result.misconception,
        resource_state=result.resource_state,
        decision=result.recommendation,
        explanation=result.recommendation.explanation,
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
