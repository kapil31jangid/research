"""Canonical controlled conditions without duplicating runtime algorithms."""

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

_FULL = {
    "enable_adaptation": True,
    "enable_bkt": True,
    "enable_uncertainty": True,
    "enable_forgetting": True,
    "enable_misconceptions": True,
    "enable_resource_awareness": True,
    "enable_offline_adaptation": True,
    "enable_ml": True,
}


def condition_config(config: ExperimentConfig, condition: str) -> ExperimentConfig:
    flags = dict(_FULL)
    if condition == "static_baseline":
        flags = {key: False for key in _FULL}
    elif condition == "bkt_only":
        flags.update(
            enable_uncertainty=False,
            enable_forgetting=False,
            enable_misconceptions=False,
            enable_resource_awareness=False,
            enable_offline_adaptation=False,
            enable_ml=False,
        )
    elif condition == "bkt_uncertainty":
        flags.update(
            enable_forgetting=False,
            enable_misconceptions=False,
            enable_resource_awareness=False,
            enable_offline_adaptation=False,
            enable_ml=False,
        )
    elif condition == "pedagogical_adaptive":
        flags.update(
            enable_resource_awareness=False,
            enable_offline_adaptation=False,
            enable_ml=False,
        )
    elif condition == "full_without_ml":
        flags["enable_ml"] = False
    elif condition.startswith("no_"):
        field = {
            "no_uncertainty": "enable_uncertainty",
            "no_forgetting": "enable_forgetting",
            "no_misconceptions": "enable_misconceptions",
            "no_resource_awareness": "enable_resource_awareness",
            "no_offline_adaptation": "enable_offline_adaptation",
            "no_ml": "enable_ml",
        }.get(condition)
        if field is None:
            raise ValueError(f"unknown condition: {condition}")
        flags[field] = False
    elif condition != "full":
        raise ValueError(f"unknown condition: {condition}")
    return ExperimentConfig.model_validate(config.model_dump() | {"condition": condition} | flags)
