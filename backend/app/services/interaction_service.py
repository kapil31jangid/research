"""Transactional learner interaction processing and adaptive decision orchestration."""

import json
from datetime import UTC, datetime
from math import sqrt
from time import perf_counter_ns

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assessment.answer_evaluator import answers_equivalent
from app.controller.policy import ControllerInput, decide_adaptation
from app.core.config import get_settings
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
from app.models.recommendation import Recommendation
from app.recommendation.recommender import generate_recommendation, serialise_recommendation
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
    total_started = perf_counter_ns()
    try:
        states = ensure_learner_states(payload.learner_id, db, commit=False)
        state = next(item for item in states if item.concept_id == question.concept_id)
        correct = answers_equivalent(
            payload.submitted_answer, question.correct_answer, question.answer_type
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
        previous = state.attempts
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
        count = state.response_time_count + 1
        mean = state.average_response_time or 0.0
        delta = seconds - mean
        mean += delta / count
        state.response_time_m2 += delta * (seconds - mean)
        state.response_time_count = count
        state.average_response_time = mean
        state.response_time_variation = min(
            sqrt(state.response_time_m2 / (count - 1) if count > 1 else 0.0)
            / get_settings().response_time_variation_reference_seconds,
            1.0,
        )
        state.hint_usage_rate = (
            state.hint_usage_rate * previous + int(payload.hints_used > 0)
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
                .where(
                    Interaction.learner_id == payload.learner_id,
                    Interaction.concept_id == question.concept_id,
                )
                .order_by(Interaction.created_at.desc())
                .limit(get_settings().misconception_evidence_window)
            )
        )
        patterns = {
            item.id: json.loads(item.misconception_patterns)
            for item in db.scalars(
                select(Question).where(Question.id.in_([item.question_id for item in recent]))
            )
        }
        detections = detect_misconceptions(
            [
                InteractionEvidence(
                    item.concept_id,
                    item.correct,
                    patterns.get(item.question_id, []),
                    item.created_at
                    if item.created_at.tzinfo
                    else item.created_at.replace(tzinfo=UTC),
                )
                for item in recent
            ],
            load_rules(),
            get_settings(),
        )
        misconception = detections[0] if detections else None
        state.suspected_misconception = misconception.id if misconception else None
        state.misconception_confidence = misconception.confidence if misconception else 0.0
        controller_started = perf_counter_ns()
        mastery = {item.concept_id: item.mastery_probability for item in states}
        cached = payload.offline_content
        relevant_cache = bool(
            cached
            and cached.app_shell_available
            and (
                question.concept_id in cached.cached_concept_ids
                or bool(set(cached.cached_activity_ids))
            )
        )
        controller_input = ControllerInput(
            state.misconception_confidence,
            prerequisite_mastery(build_graph(load_concepts()), question.concept_id, mastery),
            state.uncertainty,
            serialise_state(state).retained_mastery,
            sum(item.attempts for item in states),
            resource,
            offline_cache_available=relevant_cache,
        )
        decision = decide_adaptation(controller_input)
        controller_latency = (perf_counter_ns() - controller_started) / 1_000_000
        recommendation_started = perf_counter_ns()
        recommendation = generate_recommendation(
            payload.learner_id,
            states,
            question.concept_id,
            controller_input,
            decision,
            db,
            commit=False,
        )
        record = db.get(Recommendation, recommendation.id)
        record.measured_controller_latency_ms = controller_latency
        record.measured_recommendation_latency_ms = (
            perf_counter_ns() - recommendation_started
        ) / 1_000_000
        record.measured_total_adaptive_latency_ms = (perf_counter_ns() - total_started) / 1_000_000
        db.commit()
        db.refresh(interaction)
        db.refresh(record)
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
            serialise_recommendation(record),
        )
    except Exception:
        db.rollback()
        raise
