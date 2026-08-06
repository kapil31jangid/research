"""Persist ranked, explainable recommendations and alternatives."""

import json
from dataclasses import replace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.controller.explanation import explain_decision
from app.controller.policy import ControllerDecision, ControllerInput
from app.ml_runtime.model_registry import get_response_predictor_registry
from app.ml_runtime.schemas import ResponsePredictionFeatures
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
        triggered_rules=json.loads(item.triggered_rules),
        rejected_paths=json.loads(item.rejected_paths),
        offline_content_available=item.offline_content_available,
        matching_offline_activity_ids=json.loads(item.matching_offline_activity_ids),
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
    candidate_probabilities: dict[str, float] | None = None,
    allowed_activity_ids: set[str] | None = None,
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
        states,
        concepts,
        focus_concept_id,
        decision.adaptation_path,
        recent_activity_ids,
        allowed_activity_ids,
    )
    if not candidates:
        candidates = generate_candidates(
            states,
            concepts,
            focus_concept_id,
            decision.adaptation_path,
            set(),
            allowed_activity_ids,
        )
    candidate_probabilities = candidate_probabilities or {}
    if decision.adaptation_path == "lightweight_ml_recommendation" and not candidate_probabilities:
        registry = get_response_predictor_registry()
        state_by_concept = {state.concept_id: state for state in states}
        for candidate in candidates:
            state = state_by_concept[candidate.concept_id]
            candidate_probabilities[candidate.activity_id] = registry.predict_probability(
                ResponsePredictionFeatures(
                    mastery=state.mastery_probability,
                    retained_mastery=state.mastery_probability,
                    uncertainty=state.uncertainty,
                    question_difficulty=float(candidate.expected_learning_gain),
                    concept_difficulty=float(candidate.expected_learning_gain),
                    recent_correctness=0.0,
                    average_response_time=state.average_response_time or 0.0,
                    response_time_variation=state.response_time_variation,
                    hint_usage_rate=state.hint_usage_rate,
                    attempts=float(state.attempts),
                    correct_attempts=float(state.correct_attempts),
                    prerequisite_mastery=candidate.prerequisite_relevance,
                    days_since_practice=0.0,
                    misconception_confidence=state.misconception_confidence,
                    resource_score=controller_input.resource.score,
                )
            )
    candidates = [
        replace(
            candidate,
            predicted_correctness_probability=candidate_probabilities.get(candidate.activity_id),
        )
        for candidate in candidates
    ]
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
        triggered_rules=json.dumps(decision.triggered_rules),
        rejected_paths=json.dumps(decision.rejected_paths),
        offline_content_available=controller_input.offline_cache_available,
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
