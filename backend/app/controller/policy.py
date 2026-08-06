"""Deterministic, explainable policy for selecting adaptation mechanisms."""

from dataclasses import dataclass
from typing import Literal

from app.core.config import Settings, get_settings
from app.resources.scoring import ResourceSnapshot

AdaptationPath = Literal[
    "diagnostic_assessment",
    "misconception_remediation",
    "prerequisite_review",
    "spaced_review",
    "rule_based_recommendation",
    "bkt_based_recommendation",
    "lightweight_ml_recommendation",
    "cached_offline_recommendation",
]


@dataclass(frozen=True)
class ControllerInput:
    misconception_confidence: float
    prerequisite_mastery: float
    uncertainty: float
    retained_mastery: float
    interaction_count: int
    resource: ResourceSnapshot
    offline_cache_available: bool = False
    ml_model_available: bool = False


@dataclass(frozen=True)
class ControllerDecision:
    adaptation_path: AdaptationPath
    reason: str
    triggered_rules: list[str]
    rejected_paths: list[str]
    estimated_computational_cost_ms: float
    decision_confidence: float
    resource_score: float


_COST_MS: dict[AdaptationPath, float] = {
    "diagnostic_assessment": 1.0,
    "misconception_remediation": 2.0,
    "prerequisite_review": 1.5,
    "spaced_review": 1.5,
    "rule_based_recommendation": 1.0,
    "bkt_based_recommendation": 3.0,
    "lightweight_ml_recommendation": 8.0,
    "cached_offline_recommendation": 0.5,
}


def decide_adaptation(
    state: ControllerInput, settings: Settings | None = None
) -> ControllerDecision:
    """Apply the specified policy in priority order and reveal its reasoning."""
    configuration = settings or get_settings()
    candidates: list[tuple[bool, AdaptationPath, str, str]] = [
        (
            state.misconception_confidence >= configuration.high_misconception_threshold,
            "misconception_remediation",
            "high_misconception",
            "Repeated error evidence indicates a high-confidence misconception.",
        ),
        (
            state.prerequisite_mastery < configuration.prerequisite_mastery_threshold,
            "prerequisite_review",
            "prerequisite_gap",
            "Required prerequisite mastery is below the configured threshold.",
        ),
        (
            state.uncertainty >= configuration.high_uncertainty_threshold,
            "diagnostic_assessment",
            "high_uncertainty",
            "The learner estimate needs additional diagnostic evidence.",
        ),
        (
            state.retained_mastery < configuration.retained_mastery_threshold,
            "spaced_review",
            "retention_need",
            "Retained mastery is below the configured review threshold.",
        ),
        (
            state.resource.level == "critical" and state.offline_cache_available,
            "cached_offline_recommendation",
            "critical_resources_cached_content",
            "Critical resources require a cached offline recommendation.",
        ),
        (
            state.resource.level == "critical",
            "rule_based_recommendation",
            "critical_resources",
            "Critical resources allow only a minimal rule-based recommendation.",
        ),
        (
            state.resource.level == "low",
            "rule_based_recommendation",
            "low_resources",
            "Low resources favour a reliable low-cost rule-based recommendation.",
        ),
        (
            state.resource.level == "moderate",
            "bkt_based_recommendation",
            "moderate_resources",
            "Moderate resources can afford BKT-based recommendation.",
        ),
        (
            state.resource.level == "high"
            and state.interaction_count >= configuration.ml_minimum_interactions
            and state.ml_model_available,
            "lightweight_ml_recommendation",
            "high_resources_sufficient_history",
            "High resources and sufficient history permit lightweight ML.",
        ),
    ]
    selected_index, selected = next(
        ((index, candidate) for index, candidate in enumerate(candidates) if candidate[0]),
        (
            len(candidates),
            (True, "bkt_based_recommendation", "default_bkt", "BKT is the safe default."),
        ),
    )
    _, path, rule, reason = selected
    rejected = [candidate[1] for candidate in candidates[selected_index + 1 :] if candidate[0]]
    confidence = min(1.0, 0.65 + 0.25 * (1.0 - state.uncertainty))
    return ControllerDecision(
        adaptation_path=path,
        reason=reason,
        triggered_rules=[rule],
        rejected_paths=rejected,
        estimated_computational_cost_ms=_COST_MS[path],
        decision_confidence=confidence,
        resource_score=state.resource.score,
    )
