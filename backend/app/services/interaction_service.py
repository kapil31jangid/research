"""Transactional learner interaction processing and adaptive decision orchestration."""

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from time import perf_counter_ns

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assessment.answer_evaluator import answers_equivalent
from app.controller.policy import ControllerDecision, ControllerInput, decide_adaptation
from app.core.config import get_settings
from app.curriculum.graph import build_graph, prerequisite_ids
from app.curriculum.loader import load_concepts
from app.curriculum.prerequisites import prerequisite_mastery
from app.curriculum.registry import get_curriculum_context
from app.evaluation.policy import EvaluationPolicy
from app.learner_model.bkt import update_mastery
from app.learner_model.response_time import update_response_time_statistics
from app.learner_model.state import parameters_for_concept
from app.learner_model.uncertainty import calculate_uncertainty
from app.misconceptions.detector import InteractionEvidence, detect_misconceptions
from app.misconceptions.rules import load_rules
from app.ml_runtime.exceptions import ResponsePredictionError
from app.ml_runtime.model_registry import get_response_predictor_registry
from app.models.activity import LearningActivity
from app.models.interaction import Interaction
from app.models.learner_state import MasteryHistory
from app.models.question import Question
from app.models.recommendation import Recommendation
from app.offline.content_availability import resolve_offline_availability
from app.recommendation.recommender import generate_recommendation, serialise_recommendation
from app.resources.monitor import current_resources
from app.resources.scoring import ResourceSnapshot, snapshot_from_measurements
from app.schemas.interactions import (
    InteractionCreate,
    InteractionCurriculumContext,
    InteractionRead,
    MisconceptionRead,
)
from app.schemas.recommendations import RecommendationRead
from app.schemas.resources import ResourceStateRead
from app.schemas.state import LearnerConceptStateRead
from app.services.learner_service import (
    active_concept_ids,
    ensure_learner_states,
    serialise_state,
)


@dataclass(frozen=True)
class ProcessedInteraction:
    interaction: InteractionRead
    learner_state: LearnerConceptStateRead
    misconception: MisconceptionRead
    resource_state: ResourceStateRead
    recommendation: RecommendationRead


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
        curriculum_context=InteractionCurriculumContext(
            board_id=interaction.board_id,
            class_level=interaction.class_level,
            subject_id=interaction.subject_id,
            book_id=interaction.book_id,
            chapter_id=interaction.chapter_id,
            curriculum_pack_version=interaction.curriculum_pack_version,
        ),
        created_at=interaction.created_at,
    )


def _create_interaction_record(
    payload: InteractionCreate, question: Question, correct: bool, resource: ResourceSnapshot
) -> Interaction:
    """Build the pending interaction event without committing it."""
    context = get_curriculum_context(question.concept_id)
    return Interaction(
        learner_id=payload.learner_id,
        question_id=question.id,
        concept_id=question.concept_id,
        submitted_answer=payload.submitted_answer,
        correct=correct,
        response_time_ms=payload.response_time_ms,
        hints_used=payload.hints_used,
        resource_state=json.dumps(resource.__dict__),
        offline=payload.offline or resource.offline,
        board_id=context.board_id,
        class_level=context.class_level,
        subject_id=context.subject_id,
        book_id=context.book_id,
        chapter_id=context.chapter_id,
        curriculum_pack_version=context.curriculum_pack_version,
    )


def process_interaction(
    payload: InteractionCreate,
    question: Question,
    db: Session,
    evaluation_policy: EvaluationPolicy | None = None,
) -> ProcessedInteraction:
    """Run validation, BKT update, misconception detection, controller, and recommendation."""
    total_started = perf_counter_ns()
    try:
        states = ensure_learner_states(
            payload.learner_id, db, commit=False, include_prerequisites=True
        )
        state = next(item for item in states if item.concept_id == question.concept_id)
        correct = answers_equivalent(
            payload.submitted_answer, question.correct_answer, question.answer_type
        )
        resource = _resource_for(payload)
        interaction = _create_interaction_record(payload, question, correct, resource)
        db.add(interaction)
        previous = state.attempts
        policy = evaluation_policy or EvaluationPolicy()
        if policy.enable_bkt:
            state.mastery_probability = update_mastery(
                state.mastery_probability,
                correct,
                parameters_for_concept(question.concept_id, question.difficulty),
            )
        else:
            new_attempts = state.attempts + 1
            state.mastery_probability = (state.correct_attempts + int(correct)) / new_attempts
        state.attempts += 1
        state.correct_attempts += int(correct)
        correctness = (json.loads(state.recent_correctness) + [correct])[-8:]
        state.recent_correctness = json.dumps(correctness)
        update_response_time_statistics(
            state,
            payload.response_time_ms,
            get_settings().response_time_variation_reference_seconds,
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
        detections = (
            detect_misconceptions(
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
            if policy.enable_misconceptions
            else []
        )
        misconception = detections[0] if detections else None
        if policy.enable_misconceptions:
            state.suspected_misconception = misconception.id if misconception else None
            state.misconception_confidence = misconception.confidence if misconception else 0.0
        controller_started = perf_counter_ns()
        mastery = {item.concept_id: item.mastery_probability for item in states}
        availability = resolve_offline_availability(
            payload.offline_content,
            list(db.scalars(select(LearningActivity))),
            question.concept_id,
            "misconception_remediation" if misconception else "cached_offline_recommendation",
            misconception.id if misconception else None,
        )
        if not policy.enable_offline_adaptation:
            availability = replace(availability, available=False, matching_activity_ids=[])
        model_registry = get_response_predictor_registry()
        controller_resource = resource
        if not policy.enable_resource_awareness:
            controller_resource = snapshot_from_measurements(
                8000, 8192, 5, 100, True, True, 1.0, 10_000, 1.0
            )
        controller_input = ControllerInput(
            state.misconception_confidence if policy.enable_misconceptions else 0.0,
            prerequisite_mastery(build_graph(load_concepts()), question.concept_id, mastery),
            state.uncertainty if policy.enable_uncertainty else 0.0,
            serialise_state(state).retained_mastery
            if policy.enable_forgetting
            else state.mastery_probability,
            sum(item.attempts for item in states),
            controller_resource,
            offline_cache_available=availability.available,
            ml_model_available=model_registry.is_available() if policy.enable_ml else False,
        )
        decision = (
            decide_adaptation(controller_input)
            if policy.enable_adaptation
            else ControllerDecision(
                adaptation_path="rule_based_recommendation",
                reason="Evaluation static baseline follows curriculum order only.",
                triggered_rules=["evaluation_static_baseline"],
                rejected_paths=[],
                estimated_computational_cost_ms=1.0,
                decision_confidence=1.0,
                resource_score=controller_resource.score,
            )
        )
        controller_latency = (perf_counter_ns() - controller_started) / 1_000_000
        recommendation_started = perf_counter_ns()
        requested_path = decision.adaptation_path
        model_version = (
            model_registry.get_model_version()
            if requested_path == "lightweight_ml_recommendation"
            else None
        )
        fallback_used = False
        fallback_reason = None
        graph = build_graph(load_concepts())
        recommendation_focus_id = question.concept_id
        static_preferred_activity_id = None
        if decision.adaptation_path == "misconception_remediation" and misconception:
            remediation_activity = db.get(LearningActivity, misconception.remediation_activity)
            if remediation_activity is not None:
                recommendation_focus_id = remediation_activity.concept_id
        if not policy.enable_adaptation:
            static_activities = sorted(
                (
                    activity
                    for activity in db.scalars(
                        select(LearningActivity).where(
                            LearningActivity.concept_id == question.concept_id,
                            LearningActivity.is_active.is_(True),
                            LearningActivity.deprecated_at.is_(None),
                        )
                    )
                    if "rule_based_recommendation" in json.loads(activity.adaptation_paths)
                ),
                key=lambda activity: activity.id,
            )
            if static_activities:
                index = (controller_input.interaction_count - 1) % len(static_activities)
                static_preferred_activity_id = static_activities[index].id
        if decision.adaptation_path == "prerequisite_review":
            required = prerequisite_ids(graph, question.concept_id)
            if required:
                recommendation_focus_id = min(required, key=lambda concept_id: mastery[concept_id])

        def build_recommendation() -> RecommendationRead:
            return generate_recommendation(
                payload.learner_id,
                states,
                recommendation_focus_id,
                controller_input,
                decision,
                db,
                commit=False,
                requested_adaptation_path=requested_path,
                ml_model_available=controller_input.ml_model_available,
                model_version=model_version,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
                allowed_activity_ids=(
                    set(availability.matching_activity_ids)
                    if decision.adaptation_path == "cached_offline_recommendation"
                    else None
                ),
                preferred_activity_id=(
                    misconception.remediation_activity
                    if decision.adaptation_path == "misconception_remediation" and misconception
                    else static_preferred_activity_id
                ),
                matching_offline_activity_ids=availability.matching_activity_ids,
                offline_content_reason=availability.reason,
                uncertainty_enabled=policy.enable_uncertainty,
                forgetting_enabled=policy.enable_forgetting,
                eligible_concept_ids=(
                    {recommendation_focus_id}
                    if decision.adaptation_path == "prerequisite_review"
                    else active_concept_ids(payload.learner_id, db)
                ),
            )

        try:
            recommendation = build_recommendation()
        except ResponsePredictionError as error:
            if requested_path != "lightweight_ml_recommendation":
                raise
            fallback_used = True
            fallback_reason = str(error)
            decision = replace(
                decision,
                adaptation_path="bkt_based_recommendation",
                reason="ML inference failed; BKT recommendation used safely",
            )
            recommendation = build_recommendation()
        record = db.get(Recommendation, recommendation.id)
        record.measured_controller_latency_ms = controller_latency
        record.measured_recommendation_latency_ms = (
            perf_counter_ns() - recommendation_started
        ) / 1_000_000
        record.measured_total_adaptive_latency_ms = (perf_counter_ns() - total_started) / 1_000_000
        db.commit()
        db.refresh(interaction)
        db.refresh(record)
        return ProcessedInteraction(
            interaction=_read(interaction),
            learner_state=serialise_state(state),
            misconception=MisconceptionRead(
                detected=misconception is not None,
                id=misconception.id if misconception else None,
                confidence=misconception.confidence if misconception else 0.0,
                explanation=misconception.explanation if misconception else None,
                remediation_activity=misconception.remediation_activity if misconception else None,
            ),
            resource_state=ResourceStateRead(**resource.__dict__),
            recommendation=serialise_recommendation(record),
        )
    except Exception:
        db.rollback()
        raise
