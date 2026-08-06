"""Deterministic feature construction for candidate-level ML ranking."""

import json
from datetime import UTC, datetime

from app.learner_model.forgetting import retained_mastery
from app.ml_runtime.schemas import ResponsePredictionFeatures
from app.models.activity import LearningActivity
from app.models.concept import Concept
from app.models.learner_state import LearnerConceptState
from app.recommendation.candidate_generator import ActivityCandidate


def build_candidate_prediction_features(
    *,
    candidate: ActivityCandidate,
    activity: LearningActivity,
    concept: Concept,
    learner_state: LearnerConceptState,
    prerequisite_mastery: float,
    resource_score: float,
    now: datetime,
) -> ResponsePredictionFeatures:
    """Build the trained feature schema from persisted learner and activity state."""
    current_time = now if now.tzinfo else now.replace(tzinfo=UTC)
    last_practised = learner_state.last_practised_at
    if last_practised is not None and last_practised.tzinfo is None:
        last_practised = last_practised.replace(tzinfo=UTC)
    recent = json.loads(learner_state.recent_correctness or "[]")
    days_since_practice = (
        max(0.0, (current_time - last_practised).total_seconds() / 86_400)
        if last_practised is not None
        else 0.0
    )
    return ResponsePredictionFeatures(
        mastery=learner_state.mastery_probability,
        retained_mastery=retained_mastery(
            learner_state.mastery_probability,
            last_practised,
            learner_state.forgetting_rate or 0.03,
            current_time,
        ),
        uncertainty=learner_state.uncertainty,
        question_difficulty=candidate.difficulty,
        concept_difficulty=float(concept.difficulty),
        recent_correctness=sum(bool(value) for value in recent) / len(recent) if recent else 0.0,
        average_response_time=learner_state.average_response_time or 0.0,
        response_time_variation=learner_state.response_time_variation or 0.0,
        hint_usage_rate=learner_state.hint_usage_rate or 0.0,
        attempts=float(learner_state.attempts),
        correct_attempts=float(learner_state.correct_attempts),
        prerequisite_mastery=prerequisite_mastery,
        days_since_practice=days_since_practice,
        misconception_confidence=learner_state.misconception_confidence or 0.0,
        resource_score=resource_score,
    )
