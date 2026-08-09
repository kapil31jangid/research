"""Learner-state persistence and read-model operations."""

import json
from datetime import datetime

import networkx as nx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.curriculum.graph import build_graph
from app.curriculum.loader import load_concepts
from app.curriculum.registry import concept_ids_for_subject
from app.learner_model.forgetting import retained_mastery
from app.models.concept import Concept
from app.models.learner import Learner
from app.models.learner_state import LearnerConceptState, MasteryHistory
from app.schemas.state import LearnerConceptStateRead, LearnerProgressRead


def ensure_learner_states(
    learner_id: str,
    db: Session,
    commit: bool = True,
    include_prerequisites: bool = False,
) -> list[LearnerConceptState]:
    """Create and return states scoped to the learner's active curriculum."""
    learner = db.get(Learner, learner_id)
    if learner is None or learner.active_subject_id is None:
        return []
    target_ids = concept_ids_for_subject(learner.active_subject_id)
    scoped_ids = set(target_ids)
    if include_prerequisites:
        graph = build_graph(load_concepts())
        for concept_id in target_ids:
            scoped_ids.update(nx.ancestors(graph, concept_id))
    concepts = list(
        db.scalars(select(Concept).where(Concept.id.in_(scoped_ids)).order_by(Concept.id))
    )
    existing = {
        state.concept_id
        for state in db.scalars(
            select(LearnerConceptState).where(LearnerConceptState.learner_id == learner_id)
        )
    }
    settings = get_settings()
    for concept in concepts:
        if concept.id not in existing:
            state = LearnerConceptState(
                learner_id=learner_id,
                concept_id=concept.id,
                mastery_probability=settings.default_initial_mastery,
                forgetting_rate=settings.default_forgetting_rate,
            )
            db.add(state)
            db.flush()
            db.add(
                MasteryHistory(
                    learner_id=learner_id,
                    concept_id=concept.id,
                    mastery_probability=state.mastery_probability,
                    uncertainty=state.uncertainty,
                )
            )
    if commit:
        db.commit()
    else:
        db.flush()
    return list(
        db.scalars(
            select(LearnerConceptState)
            .where(
                LearnerConceptState.learner_id == learner_id,
                LearnerConceptState.concept_id.in_(scoped_ids),
            )
            .order_by(LearnerConceptState.concept_id)
        )
    )


def active_concept_ids(learner_id: str, db: Session) -> set[str]:
    learner = db.get(Learner, learner_id)
    if learner is None or learner.active_subject_id is None:
        return set()
    return concept_ids_for_subject(learner.active_subject_id)


def serialise_state(
    state: LearnerConceptState, now: datetime | None = None
) -> LearnerConceptStateRead:
    """Apply dynamic forgetting decay while preserving stored mastery."""
    settings = get_settings()
    rate = (
        state.forgetting_rate
        if state.forgetting_rate is not None
        else settings.default_forgetting_rate
    )
    return LearnerConceptStateRead(
        concept_id=state.concept_id,
        mastery_probability=state.mastery_probability,
        retained_mastery=retained_mastery(
            state.mastery_probability, state.last_practised_at, rate, now
        ),
        uncertainty=state.uncertainty,
        attempts=state.attempts,
        correct_attempts=state.correct_attempts,
        recent_correctness=json.loads(state.recent_correctness),
        average_response_time=state.average_response_time,
        response_time_variation=state.response_time_variation,
        hint_usage_rate=state.hint_usage_rate,
        last_practised_at=state.last_practised_at,
        forgetting_rate=rate,
        suspected_misconception=state.suspected_misconception,
        misconception_confidence=state.misconception_confidence,
    )


def learner_progress(learner_id: str, db: Session) -> LearnerProgressRead:
    """Return an aggregate progress read model without mutating mastery."""
    states = [serialise_state(state) for state in ensure_learner_states(learner_id, db)]
    count = len(states)
    return LearnerProgressRead(
        learner_id=learner_id,
        concept_count=count,
        average_mastery=sum(state.mastery_probability for state in states) / count
        if count
        else 0.0,
        average_retained_mastery=sum(state.retained_mastery for state in states) / count
        if count
        else 0.0,
        average_uncertainty=sum(state.uncertainty for state in states) / count if count else 0.0,
        total_attempts=sum(state.attempts for state in states),
        states=states,
    )
