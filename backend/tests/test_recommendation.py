from app.models.concept import Concept
from app.models.learner_state import LearnerConceptState
from app.recommendation.candidate_generator import ActivityCandidate, generate_candidates
from app.recommendation.scorer import score_candidate


def test_candidate_score_rewards_need_and_penalises_cost() -> None:
    high_need = ActivityCandidate("a", "activity_a", 0.9, 1.0, 0.9, 0.8, 0.0, 0.1)
    low_need = ActivityCandidate("a", "activity_b", 0.2, 0.4, 0.2, 0.1, 0.0, 0.9)
    assert score_candidate(high_need, 0.5)[0] > score_candidate(low_need, 0.5)[0]


def test_candidate_prediction_rewards_the_learning_zone() -> None:
    zone = ActivityCandidate("a", "zone", 0.5, 0.5, 0.5, 0.5, 0.0, 0.2, 0.7)
    outside = ActivityCandidate("a", "outside", 0.5, 0.5, 0.5, 0.5, 0.0, 0.2, 0.1)
    assert score_candidate(zone, 1.0)[0] > score_candidate(outside, 1.0)[0]


def test_remediation_and_cached_paths_do_not_offer_other_concepts() -> None:
    concepts = {
        "focus": Concept(
            id="focus", name="Focus", description="", difficulty=1, activity_ids='["focus_a"]'
        ),
        "other": Concept(
            id="other", name="Other", description="", difficulty=1, activity_ids='["other_a"]'
        ),
    }
    states = [
        LearnerConceptState(
            learner_id="l", concept_id="focus", mastery_probability=0.5, uncertainty=1.0
        ),
        LearnerConceptState(
            learner_id="l", concept_id="other", mastery_probability=0.1, uncertainty=1.0
        ),
    ]
    for path in ("misconception_remediation", "cached_offline_recommendation"):
        candidates = generate_candidates(states, concepts, "focus", path, set())
        assert {candidate.concept_id for candidate in candidates} == {"focus"}


def test_recent_activities_are_excluded_when_alternatives_exist() -> None:
    concepts = {
        "focus": Concept(
            id="focus", name="Focus", description="", difficulty=1, activity_ids='["recent", "new"]'
        )
    }
    states = [
        LearnerConceptState(
            learner_id="l", concept_id="focus", mastery_probability=0.5, uncertainty=1.0
        )
    ]
    candidates = generate_candidates(
        states, concepts, "focus", "bkt_based_recommendation", {"recent"}
    )
    assert [candidate.activity_id for candidate in candidates] == ["new"]
