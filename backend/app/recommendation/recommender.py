"""Persist ranked, explainable recommendations and alternatives."""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.controller.explanation import explain_decision
from app.controller.policy import ControllerDecision, ControllerInput
from app.models.concept import Concept
from app.models.learner_state import LearnerConceptState
from app.models.recommendation import Recommendation
from app.recommendation.candidate_generator import generate_candidates
from app.recommendation.scorer import score_candidate
from app.schemas.recommendations import RecommendationAlternativeRead, RecommendationRead


def serialise_recommendation(item: Recommendation) -> RecommendationRead:
    return RecommendationRead(
        id=item.id,
        learner_id=item.learner_id,
        selected_concept_id=item.selected_concept_id,
        selected_activity_id=item.selected_activity_id,
        adaptation_path=item.adaptation_path,
        requested_adaptation_path=item.requested_adaptation_path,
        fallback_used=item.fallback_used,
        fallback_reason=item.fallback_reason,
        ml_model_available=item.ml_model_available,
        model_version=item.model_version,
        predicted_correctness_probability=item.predicted_correctness_probability,
        expected_learning_gain=item.expected_learning_gain,
        computational_cost_ms=item.computational_cost_ms,
        measured_controller_latency_ms=item.measured_controller_latency_ms,
        measured_recommendation_latency_ms=item.measured_recommendation_latency_ms,
        measured_total_adaptive_latency_ms=item.measured_total_adaptive_latency_ms,
        controller_mode=item.controller_mode,
        score=item.score,
        explanation=json.loads(item.explanation),
        alternatives=json.loads(item.alternatives),
        created_at=item.created_at,
    )


def generate_recommendation(
    learner_id: str,
    states: list[LearnerConceptState],
    focus_concept_id: str,
    controller_input: ControllerInput,
    decision: ControllerDecision,
    db: Session,
    commit: bool = True,
    requested_adaptation_path: str | None = None,
    ml_model_available: bool = False,
    model_version: str | None = None,
    predicted_correctness_probability: float | None = None,
    fallback_used: bool = False,
    fallback_reason: str | None = None,
) -> RecommendationRead:
    """Score candidates, retain at least three alternatives when available, and persist."""
    concepts = {concept.id: concept for concept in db.scalars(select(Concept))}
    previous = list(
        db.scalars(
            select(Recommendation)
            .where(Recommendation.learner_id == learner_id)
            .order_by(Recommendation.created_at.desc())
            .limit(3)
        )
    )
    recent_activity_ids = {item.selected_activity_id for item in previous}
    candidates = generate_candidates(
        states, concepts, focus_concept_id, decision.adaptation_path, recent_activity_ids
    )
    if not candidates:
        candidates = generate_candidates(
            states, concepts, focus_concept_id, decision.adaptation_path, set()
        )
    ranked = sorted(
        (
            (*score_candidate(candidate, controller_input.resource.score), candidate)
            for candidate in candidates
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    if not ranked:
        raise ValueError("No available activities for recommendation")
    score, details, selected = ranked[0]
    alternatives = [
        RecommendationAlternativeRead(
            concept_id=candidate.concept_id,
            activity_id=candidate.activity_id,
            score=candidate_score,
            explanation=candidate_details,
        )
        for candidate_score, candidate_details, candidate in ranked[1:4]
    ]
    explanation = explain_decision(decision, controller_input) + [
        f"Selected {selected.activity_id}: {details}."
    ]
    record = Recommendation(
        learner_id=learner_id,
        selected_concept_id=selected.concept_id,
        selected_activity_id=selected.activity_id,
        adaptation_path=decision.adaptation_path,
        requested_adaptation_path=requested_adaptation_path or decision.adaptation_path,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        ml_model_available=ml_model_available,
        model_version=model_version,
        predicted_correctness_probability=predicted_correctness_probability,
        expected_learning_gain=selected.expected_learning_gain,
        computational_cost_ms=decision.estimated_computational_cost_ms,
        score=score,
        explanation=json.dumps(explanation),
        alternatives=json.dumps([item.model_dump() for item in alternatives]),
        resource_state=json.dumps(controller_input.resource.__dict__),
    )
    db.add(record)
    if commit:
        db.commit()
        db.refresh(record)
    else:
        db.flush()
    return serialise_recommendation(record)
