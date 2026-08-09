"""Application configuration loaded from the environment."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings with safe local-development defaults."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="RAPID_LEARN_")
    database_url: str = "sqlite:///./rapid_learn.db"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"
    default_forgetting_rate: float = 0.03
    default_initial_mastery: float = 0.2
    resource_critical_threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    resource_low_threshold: float = Field(default=0.50, ge=0.0, le=1.0)
    resource_moderate_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    high_misconception_threshold: float = Field(default=0.70, ge=0.0, le=1.0)
    prerequisite_mastery_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    high_uncertainty_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    retained_mastery_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    ml_minimum_interactions: int = Field(default=30, ge=1)
    ml_target_success_probability: float = Field(default=0.70, ge=0.0, le=1.0)
    ml_learning_zone_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    resource_memory_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    resource_cpu_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    resource_battery_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    resource_network_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    activity_gain_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    activity_prerequisite_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    activity_retention_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    activity_information_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    activity_misconception_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    activity_cost_weight: float = Field(default=0.05, ge=0.0, le=1.0)
    activity_cost_reference_ms: float = Field(default=2.0, gt=0.0)
    response_time_variation_reference_seconds: float = Field(default=5.0, gt=0.0)
    model_artifact_path: str = "data/models/response_predictor.joblib"
    supported_model_version: str = "0.1.0"
    controller_mode: str = "deterministic"
    misconception_evidence_window: int = Field(default=8, ge=2)
    misconception_minimum_evidence: int = Field(default=2, ge=2)
    misconception_default_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_resource_thresholds(self) -> "Settings":
        if not (
            self.resource_critical_threshold
            <= self.resource_low_threshold
            <= self.resource_moderate_threshold
        ):
            raise ValueError("Resource thresholds must be ordered: critical <= low <= moderate")
        if self.misconception_minimum_evidence > self.misconception_evidence_window:
            raise ValueError("Misconception evidence count cannot exceed its window")
        resource_weight_sum = sum(
            (
                self.resource_memory_weight,
                self.resource_cpu_weight,
                self.resource_battery_weight,
                self.resource_network_weight,
            )
        )
        if abs(resource_weight_sum - 1.0) > 1e-9:
            raise ValueError("Resource-score weights must sum to 1")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
