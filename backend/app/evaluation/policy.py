"""Explicit evaluation-only switches passed through the real interaction pipeline."""

from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.evaluation.config import ExperimentConfig


@dataclass(frozen=True)
class EvaluationPolicy:
    enable_adaptation: bool = True
    enable_bkt: bool = True
    enable_uncertainty: bool = True
    enable_forgetting: bool = True
    enable_prerequisites: bool = True
    enable_misconceptions: bool = True
    enable_resource_awareness: bool = True
    enable_offline_adaptation: bool = True
    enable_ml: bool = True
    settings: Settings | None = None


def evaluation_policy_from_config(config: ExperimentConfig) -> EvaluationPolicy:
    settings = get_settings().model_copy(
        update={
            name: getattr(config, name)
            for name in (
                "resource_memory_weight",
                "resource_cpu_weight",
                "resource_battery_weight",
                "resource_network_weight",
                "activity_gain_weight",
                "activity_prerequisite_weight",
                "activity_retention_weight",
                "activity_information_weight",
                "activity_misconception_weight",
                "activity_cost_weight",
                "activity_cost_reference_ms",
                "ml_target_success_probability",
                "ml_learning_zone_weight",
                "ml_minimum_interactions",
            )
        }
    )
    return EvaluationPolicy(
        enable_adaptation=config.enable_adaptation,
        enable_bkt=config.enable_bkt,
        enable_uncertainty=config.enable_uncertainty,
        enable_forgetting=config.enable_forgetting,
        enable_prerequisites=config.enable_prerequisites,
        enable_misconceptions=config.enable_misconceptions,
        enable_resource_awareness=config.enable_resource_awareness,
        enable_offline_adaptation=config.enable_offline_adaptation,
        enable_ml=config.enable_ml,
        settings=settings,
    )
