from pathlib import Path

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
