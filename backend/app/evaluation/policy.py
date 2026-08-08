"""Explicit evaluation-only switches passed through the real interaction pipeline."""

from dataclasses import dataclass

from app.evaluation.config import ExperimentConfig


@dataclass(frozen=True)
class EvaluationPolicy:
    enable_adaptation: bool = True
    enable_bkt: bool = True
    enable_uncertainty: bool = True
    enable_forgetting: bool = True
    enable_misconceptions: bool = True
    enable_resource_awareness: bool = True
    enable_offline_adaptation: bool = True
    enable_ml: bool = True


def evaluation_policy_from_config(config: ExperimentConfig) -> EvaluationPolicy:
    return EvaluationPolicy(
        enable_adaptation=config.enable_adaptation,
        enable_bkt=config.enable_bkt,
        enable_uncertainty=config.enable_uncertainty,
        enable_forgetting=config.enable_forgetting,
        enable_misconceptions=config.enable_misconceptions,
        enable_resource_awareness=config.enable_resource_awareness,
        enable_offline_adaptation=config.enable_offline_adaptation,
        enable_ml=config.enable_ml,
    )
