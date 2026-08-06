"""Generate pedagogically appropriate, offline-safe activity candidates."""

import json
from dataclasses import dataclass

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


def generate_candidates(
    states: list[LearnerConceptState],
    concepts: dict[str, Concept],
    focus_concept_id: str,
    adaptation_path: str,
    recent_activity_ids: set[str],
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
    candidates: list[ActivityCandidate] = []
    for state in ordered_states:
        concept = concepts[state.concept_id]
        for activity_id in json.loads(concept.activity_ids):
            if activity_id in recent_activity_ids:
                continue
            candidates.append(
                ActivityCandidate(
                    concept_id=concept.id,
                    activity_id=activity_id,
                    expected_learning_gain=1.0 - state.mastery_probability,
                    prerequisite_relevance=1.0 if state.concept_id == focus_concept_id else 0.4,
                    retention_need=1.0 - state.mastery_probability,
                    information_gain=state.uncertainty,
                    misconception_relevance=(
                        state.misconception_confidence
                        if adaptation_path == "misconception_remediation"
                        else 0.0
                    ),
                    computational_cost=0.2 if "visual" not in activity_id else 0.5,
                )
            )
    return candidates
