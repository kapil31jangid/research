from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.core.config import Settings
from app.learner_model.response_predictor import (
    FEATURE_COLUMNS,
    evaluate_predictor,
    load_predictor,
    predict_correctness,
    train_predictor,
)
from app.ml_runtime.model_registry import ResponsePredictorRegistry
from app.ml_runtime.schemas import ResponsePredictionFeatures


class FixturePipeline:
    def __init__(self, probability: float = 0.5, failure: bool = False) -> None:
        self.named_steps = {"imputer": object(), "scaler": object(), "model": object()}
        self.probability = probability
        self.failure = failure

    def predict_proba(self, _frame):
        if self.failure:
            raise ValueError("fixture inference failure")
        return np.array([[1.0 - self.probability, self.probability]])


def _artifact(**updates):
    artifact = {
        "version": "0.1.0",
        "features": FEATURE_COLUMNS,
        "model": FixturePipeline(),
    }
    return artifact | updates


def test_response_predictor_trains_and_has_safe_missing_model_fallback(tmp_path: Path) -> None:
    records = []
    for index in range(20):
        record = {feature: float(index % 4) for feature in FEATURE_COLUMNS}
        record["mastery"] = index / 20
        record["correct"] = int(index >= 10)
        records.append(record)
    model = train_predictor(pd.DataFrame(records))
    metrics = evaluate_predictor(model, pd.DataFrame(records))
    assert {"accuracy", "roc_auc", "log_loss", "brier_score"} <= metrics.keys()
    assert load_predictor(tmp_path / "missing.joblib") is None
    assert predict_correctness(None, {}) is None
    assert 0.0 <= predict_correctness(model, records[0]) <= 1.0


def test_runtime_registry_validates_and_caches_a_trained_artifact(tmp_path: Path) -> None:
    records = [
        {**{feature: float(index) for feature in FEATURE_COLUMNS}, "correct": index % 2}
        for index in range(20)
    ]
    from app.learner_model.response_predictor import save_predictor

    path = tmp_path / "predictor.joblib"
    save_predictor(train_predictor(pd.DataFrame(records)), path)
    registry = ResponsePredictorRegistry(Settings(model_artifact_path=str(path)))
    assert registry.is_available()
    assert registry.get_model_version() == "0.1.0"
    assert 0 <= registry.predict_probability(ResponsePredictionFeatures(**records[0])) <= 1
    path.unlink()
    assert registry.is_available()  # successful validation is cached
    registry.reset()
    assert not registry.is_available()


def test_runtime_registry_reports_missing_artifact_reason(tmp_path: Path) -> None:
    registry = ResponsePredictorRegistry(
        Settings(model_artifact_path=str(tmp_path / "missing.joblib"))
    )
    assert not registry.is_available()
    assert registry.get_last_error_code() == "artifact_missing"
    assert registry.get_last_error_message() == "Configured model artifact is unavailable"
    registry.reset()
    assert registry.get_last_error_code() is None


def test_registry_reports_all_artifact_validation_categories(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "predictor.joblib"
    path.write_bytes(b"fixture")
    registry = ResponsePredictorRegistry(Settings(model_artifact_path=str(path)))
    cases = [
        (object(), "invalid_artifact_type"),
        (_artifact(version="9.9.9"), "unsupported_version"),
        (_artifact(features=list(reversed(FEATURE_COLUMNS))), "feature_schema_mismatch"),
        (_artifact(model=object()), "pipeline_missing"),
        (_artifact(model=FixturePipeline(failure=True)), "validation_inference_failed"),
        (_artifact(model=FixturePipeline(probability=float("nan"))), "invalid_probability"),
    ]
    for artifact, expected_code in cases:
        registry.reset()
        monkeypatch.setattr(joblib, "load", lambda _path, value=artifact: value)
        assert not registry.validate()
        assert registry.get_last_error_code() == expected_code
        assert registry.get_last_error_message()


def test_registry_reports_corrupt_artifact_and_success_clears_error(tmp_path: Path) -> None:
    path = tmp_path / "predictor.joblib"
    path.write_bytes(b"not a joblib artifact")
    registry = ResponsePredictorRegistry(Settings(model_artifact_path=str(path)))
    assert not registry.validate()
    assert registry.get_last_error_code() == "artifact_load_failed"
    joblib.dump(_artifact(), path)
    registry.reset()
    assert registry.validate()
    assert registry.get_last_error_code() is None
    assert registry.get_last_error_message() is None
