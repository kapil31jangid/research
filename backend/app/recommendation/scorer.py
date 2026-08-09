"""Transparent weighted activity-candidate scoring."""

from app.core.config import Settings, get_settings
from app.recommendation.candidate_generator import ActivityCandidate


def score_candidate(
    candidate: ActivityCandidate,
    resource_score: float,
    settings: Settings | None = None,
) -> tuple[float, str]:
    """Apply the configured initial scoring formula and describe the result."""
    configuration = settings or get_settings()
    target_probability = configuration.ml_target_success_probability
    learning_zone_score = (
        1.0 - abs(candidate.predicted_correctness_probability - target_probability)
        if candidate.predicted_correctness_probability is not None
        else 0.0
    )
    normalised_cost = min(
        max(candidate.computational_cost / configuration.activity_cost_reference_ms, 0.0),
        1.0,
    )
    score = (
        configuration.activity_gain_weight * candidate.expected_learning_gain
        + configuration.activity_prerequisite_weight * candidate.prerequisite_relevance
        + configuration.activity_retention_weight * candidate.retention_need
        + configuration.activity_information_weight * candidate.information_gain
        + configuration.activity_misconception_weight * candidate.misconception_relevance
        - configuration.activity_cost_weight * normalised_cost * (1.0 + (1.0 - resource_score))
        + configuration.ml_learning_zone_weight * min(max(learning_zone_score, 0.0), 1.0)
    )
    explanation = (
        f"gain={candidate.expected_learning_gain:.2f}, "
        f"prerequisite={candidate.prerequisite_relevance:.2f}, "
        f"retention={candidate.retention_need:.2f}, information={candidate.information_gain:.2f}, "
        f"cost_ms={candidate.computational_cost:.2f}, cost_normalised={normalised_cost:.2f}"
    )
    return score, explanation
