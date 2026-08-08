"""Named controlled conditions without duplicating controller implementation."""

from app.evaluation.config import ExperimentConfig

ABLATIONS = (
    "full",
    "no_uncertainty",
    "no_forgetting",
    "no_misconceptions",
    "no_resource_awareness",
    "no_offline_adaptation",
    "no_ml",
    "bkt_only",
    "static_baseline",
)


def condition_config(config: ExperimentConfig, condition: str) -> ExperimentConfig:
    overrides = {"condition": condition}
    if condition == "no_ml":
        overrides["enable_ml"] = False
    if condition == "no_misconceptions":
        overrides["enable_misconceptions"] = False
    if condition == "no_forgetting":
        overrides["enable_forgetting"] = False
    if condition == "no_resource_awareness":
        overrides["enable_resource_awareness"] = False
    if condition == "no_offline_adaptation":
        overrides["enable_offline_adaptation"] = False
    if condition == "no_uncertainty":
        overrides["enable_uncertainty"] = False
    if condition == "bkt_only":
        overrides.update(
            enable_ml=False, enable_misconceptions=False, enable_resource_awareness=False
        )
    if condition == "static_baseline":
        overrides.update(enable_adaptation=False, enable_bkt=False, enable_ml=False)
    return config.model_copy(update=overrides)
