"""Transparent weighted activity-candidate scoring."""

from app.core.config import get_settings
from app.recommendation.candidate_generator import ActivityCandidate


def score_candidate(candidate: ActivityCandidate, resource_score: float) -> tuple[float, str]:
    """Apply the configured initial scoring formula and describe the result."""
    settings = get_settings()
    target_probability = settings.ml_target_success_probability
    learning_zone_score = (
        1.0 - abs(candidate.predicted_correctness_probability - target_probability)
        if candidate.predicted_correctness_probability is not None
        else 0.0
    )
    score = (
        0.30 * candidate.expected_learning_gain
        + 0.20 * candidate.prerequisite_relevance
        + 0.20 * candidate.retention_need
        + 0.15 * candidate.information_gain
        + 0.10 * candidate.misconception_relevance
        - 0.05 * candidate.computational_cost * (1.0 + (1.0 - resource_score))
        + settings.ml_learning_zone_weight * min(max(learning_zone_score, 0.0), 1.0)
    )
    explanation = (
        f"gain={candidate.expected_learning_gain:.2f}, "
        f"prerequisite={candidate.prerequisite_relevance:.2f}, "
        f"retention={candidate.retention_need:.2f}, information={candidate.information_gain:.2f}, "
        f"cost={candidate.computational_cost:.2f}"
    )
    return score, explanation
