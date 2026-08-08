"""Typed, serialisable configuration for synthetic RAPID-Learn experiments."""

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Condition = Literal[
    "static_baseline",
    "bkt_only",
    "bkt_uncertainty",
    "pedagogical_adaptive",
    "full_without_ml",
    "full",
    "no_resource_awareness",
    "no_misconceptions",
    "no_forgetting",
    "no_offline_adaptation",
    "no_uncertainty",
    "no_ml",
]


class ExperimentConfig(BaseModel):
    experiment_name: str = "rapid-learn"
    random_seed: int = 42
    learner_count: int = Field(default=10, gt=0)
    interactions_per_learner: int = Field(default=10, gt=0)
    mastery_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    condition: Condition = "full"
    resource_profile: str = "mixed"
    learner_profile_distribution: dict[str, float] = Field(default_factory=lambda: {"mixed": 1.0})
    output_dir: str = "artifacts/experiments"
    save_interaction_level_data: bool = True
    save_candidate_prediction_summary: bool = True
    synthetic_misconception_resolution_threshold: float = Field(default=0.2, ge=0.0, le=1.0)
    max_interactions_without_override: int = Field(default=100_000, gt=0)
    bootstrap_samples: int = Field(default=10_000, ge=100, le=1_000_000)
    suite_workers: int = Field(default=1, ge=1, le=64)
    enable_adaptation: bool = True
    enable_bkt: bool = True
    enable_uncertainty: bool = True
    enable_forgetting: bool = True
    enable_misconceptions: bool = True
    enable_resource_awareness: bool = True
    enable_offline_adaptation: bool = True
    enable_ml: bool = True

    @model_validator(mode="after")
    def validate_distribution(self) -> "ExperimentConfig":
        total = sum(self.learner_profile_distribution.values())
        if not self.learner_profile_distribution or abs(total - 1.0) > 1e-6:
            raise ValueError("learner profile probabilities must sum to 1")
        if Path(self.output_dir).is_absolute() and "artifacts" not in Path(self.output_dir).parts:
            raise ValueError("output_dir must be an artifacts directory")
        return self

    @property
    def config_hash(self) -> str:
        encoded = json.dumps(self.model_dump(mode="json"), sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()[:12]
