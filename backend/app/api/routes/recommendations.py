"""Recommendation retrieval and explicit generation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.controller.policy import ControllerInput, decide_adaptation
from app.curriculum.graph import build_graph
from app.curriculum.loader import load_concepts
from app.curriculum.prerequisites import prerequisite_mastery
from app.database.session import get_db
from app.models.learner import Learner
from app.models.recommendation import Recommendation
from app.recommendation.recommender import generate_recommendation, serialise_recommendation
from app.resources.monitor import current_resources
from app.schemas.recommendations import GenerateRecommendationRequest, RecommendationRead
from app.services.learner_service import active_concept_ids, ensure_learner_states, serialise_state

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{learner_id}", response_model=list[RecommendationRead])
async def list_recommendations(
    learner_id: str, db: Session = Depends(get_db)
) -> list[RecommendationRead]:
    learner = db.get(Learner, learner_id)
    if learner is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return [
        serialise_recommendation(item)
        for item in db.scalars(
            select(Recommendation)
            .where(
                Recommendation.learner_id == learner_id,
                Recommendation.subject_id == learner.active_subject_id,
            )
            .order_by(Recommendation.created_at.desc())
        )
    ]


@router.post("/generate", response_model=RecommendationRead)
async def generate(
    payload: GenerateRecommendationRequest, db: Session = Depends(get_db)
) -> RecommendationRead:
    if db.get(Learner, payload.learner_id) is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    states = ensure_learner_states(payload.learner_id, db, include_prerequisites=True)
    pathway_ids = active_concept_ids(payload.learner_id, db)
    active_states = [state for state in states if state.concept_id in pathway_ids]
    if not active_states:
        raise HTTPException(status_code=404, detail="No available curriculum pathway")
    focus = payload.concept_id or max(active_states, key=lambda state: state.uncertainty).concept_id
    if focus not in pathway_ids:
        raise HTTPException(status_code=422, detail="Concept is outside the active pathway")
    state = next((item for item in states if item.concept_id == focus), None)
    if state is None:
        raise HTTPException(status_code=404, detail="Concept state not found")
    mastery = {item.concept_id: item.mastery_probability for item in states}
    resource = current_resources()
    controller_input = ControllerInput(
        state.misconception_confidence,
        prerequisite_mastery(build_graph(load_concepts()), focus, mastery),
        state.uncertainty,
        serialise_state(state).retained_mastery,
        sum(item.attempts for item in states),
        resource,
        offline_cache_available=True,
    )
    return generate_recommendation(
        payload.learner_id,
        states,
        focus,
        controller_input,
        decide_adaptation(controller_input),
        db,
        eligible_concept_ids=pathway_ids,
    )
