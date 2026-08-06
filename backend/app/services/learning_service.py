"""Diagnostic and spaced-review selection over learner state and curriculum gates."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum.graph import build_graph
from app.curriculum.loader import load_concepts
from app.curriculum.prerequisites import (
    next_eligible_concepts,
    prerequisite_mastery,
    prerequisite_status,
)
from app.models.concept import Concept
from app.models.question import Question
from app.schemas.learning import LearningPlanRead, LearningSelectionRead
from app.schemas.question import QuestionRead
from app.services.learner_service import ensure_learner_states, serialise_state
from app.services.question_service import serialise_question


def learning_plan(learner_id: str, db: Session) -> LearningPlanRead:
    """Describe eligible, revision-needed, and prerequisite-blocked concepts."""
    states = ensure_learner_states(learner_id, db)
    concepts = list(db.scalars(select(Concept)))
    mastery = {state.concept_id: state.mastery_probability for state in states}
    thresholds = {concept.id: concept.mastery_threshold for concept in concepts}
    graph = build_graph(load_concepts())
    ready = next_eligible_concepts(graph, mastery, thresholds)
    revision = [
        state.concept_id
        for state in states
        if state.mastery_probability >= thresholds[state.concept_id]
        and serialise_state(state).retained_mastery < thresholds[state.concept_id]
    ]
    blocked = [
        concept.id
        for concept in concepts
        if concept.id not in ready
        and concept.id not in revision
        and not prerequisite_status(graph, concept.id, mastery, thresholds).eligible
    ]
    return LearningPlanRead(
        learner_id=learner_id,
        ready_concept_ids=sorted(ready),
        revision_concept_ids=sorted(revision),
        blocked_concept_ids=sorted(blocked),
    )


def select_next_question(learner_id: str, db: Session) -> LearningSelectionRead | None:
    """Prefer due spaced review; otherwise select a high-information eligible diagnostic."""
    states = ensure_learner_states(learner_id, db)
    concepts = {concept.id: concept for concept in db.scalars(select(Concept))}
    mastery = {state.concept_id: state.mastery_probability for state in states}
    thresholds = {concept_id: concept.mastery_threshold for concept_id, concept in concepts.items()}
    graph = build_graph(load_concepts())
    due = sorted(
        (
            state
            for state in states
            if state.mastery_probability >= thresholds[state.concept_id]
            and serialise_state(state).retained_mastery < thresholds[state.concept_id]
        ),
        key=lambda state: serialise_state(state).retained_mastery,
    )
    if due:
        selected_state = due[0]
        selection_type = "spaced_review"
        rationale = (
            "Previously mastered content has a retained-mastery estimate below its threshold."
        )
    else:
        eligible = next_eligible_concepts(graph, mastery, thresholds)
        candidates = [state for state in states if state.concept_id in eligible]
        if not candidates:
            return None
        selected_state = max(candidates, key=lambda state: (state.uncertainty, -state.attempts))
        selection_type = "diagnostic_assessment"
        rationale = "This eligible concept has the highest current uncertainty and needs evidence."
    question = db.scalar(
        select(Question)
        .where(Question.concept_id == selected_state.concept_id)
        .order_by(Question.diagnostic_value.desc(), Question.id)
    )
    if question is None:
        return None
    prerequisite = prerequisite_mastery(graph, selected_state.concept_id, mastery)
    return LearningSelectionRead(
        learner_id=learner_id,
        selection_type=selection_type,
        concept_id=selected_state.concept_id,
        question=QuestionRead.model_validate(serialise_question(question)),
        rationale=rationale,
        prerequisite_mastery=prerequisite,
    )
