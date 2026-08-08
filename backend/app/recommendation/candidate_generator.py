"""Generate pedagogically appropriate, offline-safe activity candidates."""

import json
from dataclasses import dataclass

from app.models.activity import LearningActivity
from app.models.concept import Concept
from app.models.learner_state import LearnerConceptState


@dataclass(frozen=True)
class ActivityCandidate:
    concept_id: str
    activity_id: str
    expected_learning_gain: float
    prerequisite_relevance: float
    retention_need: float
    information_gain: float
    misconception_relevance: float
    computational_cost: float
    predicted_correctness_probability: float | None = None
    activity_type: str = "practice_quiz"
    difficulty: float = 1.0
    estimated_computational_cost_ms: float = 1.0
    available_offline: bool = False
    adaptation_paths: tuple[str, ...] = ()
    misconception_ids: tuple[str, ...] = ()


def generate_candidates(
    states: list[LearnerConceptState],
    concepts: dict[str, Concept],
    focus_concept_id: str,
    adaptation_path: str,
    recent_activity_ids: set[str],
    allowed_activity_ids: set[str] | None = None,
    preferred_activity_id: str | None = None,
    activities: list[LearningActivity] | None = None,
    uncertainty_enabled: bool = True,
) -> list[ActivityCandidate]:
    """Rank source concepts by need and expose their distinct available activities."""
    ordered_states = sorted(
        states,
        key=lambda state: (
            state.concept_id != focus_concept_id,
            state.mastery_probability,
            -state.uncertainty,
        ),
    )
    activities_by_concept: dict[str, list[LearningActivity]] = {}
    for activity in activities or []:
        activities_by_concept.setdefault(activity.concept_id, []).append(activity)
    candidates: list[ActivityCandidate] = []
    for state in ordered_states:
        if adaptation_path in {"misconception_remediation", "cached_offline_recommendation"} and (
            state.concept_id != focus_concept_id
        ):
            continue
        concept = concepts[state.concept_id]
        source = activities_by_concept.get(concept.id)
        if source is None:
            continue
        for activity in source:
            paths = tuple(json.loads(activity.adaptation_paths))
            misconceptions = tuple(json.loads(activity.misconception_ids))
            if activity.is_active is False or activity.deprecated_at is not None:
                continue
            if adaptation_path not in paths:
                continue
            activity_id = activity.id
            # A detected misconception has a rule-owned remediation activity.  Do
            # not dilute that pedagogical intervention with unrelated practice.
            if preferred_activity_id is not None and activity_id != preferred_activity_id:
                continue
            if allowed_activity_ids is not None and activity_id not in allowed_activity_ids:
                continue
            if activity_id in recent_activity_ids:
                continue
            candidates.append(
                ActivityCandidate(
                    concept_id=concept.id,
                    activity_id=activity_id,
                    expected_learning_gain=1.0 - state.mastery_probability,
                    prerequisite_relevance=1.0 if state.concept_id == focus_concept_id else 0.4,
                    retention_need=1.0 - state.mastery_probability,
                    information_gain=state.uncertainty if uncertainty_enabled else 0.0,
                    misconception_relevance=(
                        state.misconception_confidence
                        if adaptation_path == "misconception_remediation"
                        else 0.0
                    ),
                    computational_cost=activity.estimated_computational_cost_ms,
                    activity_type=activity.activity_type,
                    difficulty=float(activity.difficulty),
                    estimated_computational_cost_ms=activity.estimated_computational_cost_ms,
                    available_offline=activity.available_offline,
                    adaptation_paths=paths,
                    misconception_ids=misconceptions,
                )
            )
    return candidates
