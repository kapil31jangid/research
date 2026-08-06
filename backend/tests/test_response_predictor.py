from pathlib import Path

import pandas as pd

from app.learner_model.response_predictor import (
    FEATURE_COLUMNS,
    evaluate_predictor,
    load_predictor,
    predict_correctness,
    train_predictor,
)


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
