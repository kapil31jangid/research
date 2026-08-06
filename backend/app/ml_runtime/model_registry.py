"""Lazy, validated loader for the trained response-predictor artefact."""

from pathlib import Path

import numpy as np
import pandas as pd

from app.core.config import Settings, get_settings
from app.learner_model.response_predictor import FEATURE_COLUMNS
from app.ml_runtime.exceptions import ResponsePredictionError
from app.ml_runtime.schemas import ResponsePredictionFeatures


class ResponsePredictorRegistry:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._artifact: dict[str, object] | None = None
        self._attempted = False

    def reset(self) -> None:
        self._artifact = None
        self._attempted = False

    def validate(self) -> bool:
        if self._attempted:
            return self._artifact is not None
        self._attempted = True
        try:
            import joblib

            artifact = joblib.load(Path(self.settings.model_artifact_path))
            if (
                not isinstance(artifact, dict)
                or artifact.get("version") != self.settings.supported_model_version
            ):
                return False
            if artifact.get("features") != FEATURE_COLUMNS:
                return False
            model = artifact.get("model")
            if not hasattr(model, "predict_proba") or not hasattr(model, "named_steps"):
                return False
            if not {"imputer", "scaler", "model"} <= set(model.named_steps):
                return False
            self._artifact = artifact
            self.predict_probability(
                ResponsePredictionFeatures(**dict.fromkeys(FEATURE_COLUMNS, 0.0))
            )
            return True
        except Exception:
            self._artifact = None
            return False

    def is_available(self) -> bool:
        return self.validate()

    def get_model_version(self) -> str | None:
        return str(self._artifact["version"]) if self.validate() else None

    def predict_probability(self, features: ResponsePredictionFeatures) -> float:
        if not self.validate() or self._artifact is None:
            raise ResponsePredictionError("Response predictor is unavailable or invalid")
        try:
            model = self._artifact["model"]
            probability = float(model.predict_proba(pd.DataFrame([features.model_dump()]))[0, 1])
        except Exception as error:
            raise ResponsePredictionError("Response prediction failed") from error
        if not np.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise ResponsePredictionError("Response prediction is outside [0, 1]")
        return probability
