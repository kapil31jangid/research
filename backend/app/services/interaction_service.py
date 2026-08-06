"""Transactional learner interaction processing and adaptive decision orchestration."""

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.controller.policy import ControllerInput, decide_adaptation
from app.curriculum.graph import build_graph
from app.curriculum.loader import load_concepts
from app.curriculum.prerequisites import prerequisite_mastery
from app.learner_model.bkt import update_mastery
from app.learner_model.state import parameters_for_concept
from app.learner_model.uncertainty import calculate_uncertainty
from app.misconceptions.detector import InteractionEvidence, detect_misconceptions
from app.misconceptions.rules import load_rules
from app.models.interaction import Interaction
from app.models.learner_state import MasteryHistory
from app.models.question import Question
from app.recommendation.recommender import generate_recommendation
from app.resources.monitor import current_resources
from app.resources.scoring import ResourceSnapshot, snapshot_from_measurements
from app.schemas.interactions import InteractionCreate, InteractionRead, MisconceptionRead
from app.schemas.resources import ResourceStateRead
from app.schemas.state import LearnerConceptStateRead
from app.services.learner_service import ensure_learner_states, serialise_state


def _resource_for(payload: InteractionCreate) -> ResourceSnapshot:
    if payload.device_resource_state is None:
        return current_resources()
    value = payload.device_resource_state
    return snapshot_from_measurements(
        value.available_memory_mb,
        value.total_memory_mb,
        value.cpu_percent,
        value.battery_percent,
        value.battery_charging,
        value.network_available,
        value.network_quality,
        value.storage_available_mb,
        value.inference_latency_ms,
    )


def _read(interaction: Interaction) -> InteractionRead:
    return InteractionRead(
        id=interaction.id,
        learner_id=interaction.learner_id,
        question_id=interaction.question_id,
        concept_id=interaction.concept_id,
        submitted_answer=interaction.submitted_answer,
        correct=interaction.correct,
        response_time_ms=interaction.response_time_ms,
        hints_used=interaction.hints_used,
        offline=interaction.offline,
        created_at=interaction.created_at,
    )


def process_interaction(
    payload: InteractionCreate, question: Question, db: Session
) -> tuple[InteractionRead, LearnerConceptStateRead, MisconceptionRead, ResourceStateRead, object]:
    """Run validation, BKT update, misconception detection, controller, and recommendation."""
    states = ensure_learner_states(payload.learner_id, db)
    state = next(item for item in states if item.concept_id == question.concept_id)
    correct = (
        payload.submitted_answer.strip().casefold() == question.correct_answer.strip().casefold()
    )
    resource = _resource_for(payload)
    interaction = Interaction(
        learner_id=payload.learner_id,
        question_id=question.id,
        concept_id=question.concept_id,
        submitted_answer=payload.submitted_answer,
        correct=correct,
        response_time_ms=payload.response_time_ms,
        hints_used=payload.hints_used,
        resource_state=json.dumps(resource.__dict__),
        offline=payload.offline or resource.offline,
    )
    db.add(interaction)
    previous_attempts = state.attempts
    state.mastery_probability = update_mastery(
        state.mastery_probability,
        correct,
        parameters_for_concept(question.concept_id, question.difficulty),
    )
    state.attempts += 1
    state.correct_attempts += int(correct)
    correctness = (json.loads(state.recent_correctness) + [correct])[-8:]
    state.recent_correctness = json.dumps(correctness)
    seconds = payload.response_time_ms / 1000
    state.average_response_time = (
        seconds
        if state.average_response_time is None
        else (state.average_response_time * previous_attempts + seconds) / state.attempts
    )
    state.hint_usage_rate = (
        state.hint_usage_rate * previous_attempts + int(payload.hints_used > 0)
    ) / state.attempts
    state.uncertainty = calculate_uncertainty(
        "heuristic",
        state.mastery_probability,
        state.attempts,
        correctness,
        state.response_time_variation,
    )
    state.last_practised_at = datetime.now(UTC)
    db.add(
        MasteryHistory(
            learner_id=payload.learner_id,
            concept_id=question.concept_id,
            mastery_probability=state.mastery_probability,
            uncertainty=state.uncertainty,
            observed_correctness=correct,
        )
    )
    db.flush()
    recent = list(
        db.scalars(
            select(Interaction)
            .where(Interaction.learner_id == payload.learner_id)
            .order_by(Interaction.created_at.desc())
            .limit(8)
        )
    )
    question_patterns = {
        item.id: json.loads(item.misconception_patterns)
        for item in db.scalars(
            select(Question).where(Question.id.in_([item.question_id for item in recent]))
        )
    }
    evidence = [
        InteractionEvidence(
            item.concept_id,
            item.correct,
            question_patterns.get(item.question_id, []),
            item.created_at,
        )
        for item in recent
    ]
    detected = detect_misconceptions(evidence, load_rules())
    misconception = detected[0] if detected else None
    state.suspected_misconception = misconception.id if misconception else None
    state.misconception_confidence = misconception.confidence if misconception else 0.0
    mastery = {item.concept_id: item.mastery_probability for item in states}
    prerequisite = prerequisite_mastery(build_graph(load_concepts()), question.concept_id, mastery)
    controller_input = ControllerInput(
        state.misconception_confidence,
        prerequisite,
        state.uncertainty,
        serialise_state(state).retained_mastery,
        sum(item.attempts for item in states),
        resource,
        offline_cache_available=True,
    )
    decision = decide_adaptation(controller_input)
    recommendation = generate_recommendation(
        payload.learner_id, states, question.concept_id, controller_input, decision, db
    )
    db.refresh(interaction)
    return (
        _read(interaction),
        serialise_state(state),
        MisconceptionRead(
            detected=misconception is not None,
            id=misconception.id if misconception else None,
            confidence=misconception.confidence if misconception else 0.0,
            explanation=misconception.explanation if misconception else None,
            remediation_activity=misconception.remediation_activity if misconception else None,
        ),
        ResourceStateRead(**resource.__dict__),
        recommendation,
    )
