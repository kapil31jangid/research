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
        self._last_error_code: str | None = None
        self._last_error_message: str | None = None

    def reset(self) -> None:
        self._artifact = None
        self._attempted = False
        self._last_error_code = None
        self._last_error_message = None

    def get_last_error_code(self) -> str | None:
        return self._last_error_code

    def get_last_error_message(self) -> str | None:
        return self._last_error_message

    def _fail(self, code: str, message: str) -> bool:
        self._artifact = None
        self._last_error_code = code
        self._last_error_message = message
        return False

    def validate(self) -> bool:
        if self._attempted:
            return self._artifact is not None
        self._attempted = True
        path = Path(self.settings.model_artifact_path)
        if not path.exists():
            return self._fail("artifact_missing", "Configured model artifact is unavailable")
        try:
            import joblib

            artifact = joblib.load(path)
            if not isinstance(artifact, dict):
                return self._fail(
                    "invalid_artifact_type", "Model artifact has an unsupported shape"
                )
            if artifact.get("version") != self.settings.supported_model_version:
                return self._fail("unsupported_version", "Model artifact version is unsupported")
            if artifact.get("features") != FEATURE_COLUMNS:
                return self._fail("feature_schema_mismatch", "Model feature schema does not match")
            model = artifact.get("model")
            if not hasattr(model, "predict_proba") or not hasattr(model, "named_steps"):
                return self._fail("pipeline_missing", "Model preprocessing pipeline is unavailable")
            if not {"imputer", "scaler", "model"} <= set(model.named_steps):
                return self._fail("pipeline_missing", "Model preprocessing pipeline is incomplete")
            self._artifact = artifact
            self.predict_probability(
                ResponsePredictionFeatures(**dict.fromkeys(FEATURE_COLUMNS, 0.0))
            )
            self._last_error_code = None
            self._last_error_message = None
            return True
        except ResponsePredictionError as error:
            code = (
                "invalid_probability"
                if str(error) == "Response prediction is outside [0, 1]"
                else "validation_inference_failed"
            )
            return self._fail(code, str(error))
        except Exception:
            return self._fail("artifact_load_failed", "Model artifact could not be loaded")

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


_registry: ResponsePredictorRegistry | None = None


def get_response_predictor_registry() -> ResponsePredictorRegistry:
    global _registry
    if _registry is None:
        _registry = ResponsePredictorRegistry()
    return _registry
