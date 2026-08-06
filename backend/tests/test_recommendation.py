from app.recommendation.candidate_generator import ActivityCandidate
from app.recommendation.scorer import score_candidate


def test_candidate_score_rewards_need_and_penalises_cost() -> None:
    high_need = ActivityCandidate("a", "activity_a", 0.9, 1.0, 0.9, 0.8, 0.0, 0.1)
    low_need = ActivityCandidate("a", "activity_b", 0.2, 0.4, 0.2, 0.1, 0.0, 0.9)
    assert score_candidate(high_need, 0.5)[0] > score_candidate(low_need, 0.5)[0]
