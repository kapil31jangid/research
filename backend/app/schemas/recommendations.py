"""Recommendation API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class RecommendationAlternativeRead(BaseModel):
    concept_id: str
    activity_id: str
    score: float
    explanation: str


class RecommendationRead(BaseModel):
    id: str
    learner_id: str
    selected_concept_id: str
    selected_activity_id: str
    adaptation_path: str
    requested_adaptation_path: str
    fallback_used: bool
    fallback_reason: str | None
    ml_model_available: bool
    model_version: str | None
    predicted_correctness_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Deprecated legacy interaction-level prediction; new recommendations leave it null."
        ),
    )
    selected_candidate_predicted_probability: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Canonical selected-candidate ML prediction."
    )
    candidate_prediction_summary: list[dict[str, float | str]]
    expected_learning_gain: float = Field(ge=0.0, le=1.0)
    computational_cost_ms: float = Field(ge=0.0)
    measured_controller_latency_ms: float = Field(ge=0.0)
    measured_recommendation_latency_ms: float = Field(ge=0.0)
    measured_total_adaptive_latency_ms: float = Field(ge=0.0)
    controller_mode: str
    triggered_rules: list[str]
    rejected_paths: list[str]
    offline_content_available: bool
    matching_offline_activity_ids: list[str]
    offline_content_reason: str | None
    score: float
    explanation: list[str]
    alternatives: list[RecommendationAlternativeRead]
    created_at: datetime


class GenerateRecommendationRequest(BaseModel):
    learner_id: str
    concept_id: str | None = None
