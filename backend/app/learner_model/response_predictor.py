"""Optional, lightweight logistic-regression response predictor."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS = [
    "mastery",
    "retained_mastery",
    "uncertainty",
    "question_difficulty",
    "concept_difficulty",
    "recent_correctness",
    "average_response_time",
    "response_time_variation",
    "hint_usage_rate",
    "attempts",
    "correct_attempts",
    "prerequisite_mastery",
    "days_since_practice",
    "misconception_confidence",
    "resource_score",
]


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=500, random_state=42)),
        ]
    )


def train_predictor(frame: pd.DataFrame) -> Pipeline:
    pipeline = build_pipeline()
    pipeline.fit(frame[FEATURE_COLUMNS], frame["correct"])
    return pipeline


def evaluate_predictor(model: Pipeline, frame: pd.DataFrame) -> dict[str, float]:
    probabilities = model.predict_proba(frame[FEATURE_COLUMNS])[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    actual = frame["correct"].astype(int)
    fraction, mean_prediction = calibration_curve(
        actual, probabilities, n_bins=10, strategy="uniform"
    )
    return {
        "accuracy": float(accuracy_score(actual, predictions)),
        "precision": float(precision_score(actual, predictions, zero_division=0)),
        "recall": float(recall_score(actual, predictions, zero_division=0)),
        "f1": float(f1_score(actual, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(actual, probabilities)),
        "log_loss": float(log_loss(actual, probabilities)),
        "brier_score": float(brier_score_loss(actual, probabilities)),
        "calibration_error": float(np.mean(np.abs(fraction - mean_prediction)))
        if len(fraction)
        else 0.0,
    }


def save_predictor(model: Pipeline, path: Path, version: str = "0.1.0") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"version": version, "features": FEATURE_COLUMNS, "model": model}, path)


def load_predictor(path: Path) -> Pipeline | None:
    if not path.exists():
        return None
    return joblib.load(path)["model"]


def predict_correctness(model: Pipeline | None, features: dict[str, float]) -> float | None:
    """Return a candidate-response probability, or None when no artifact is available."""
    if model is None:
        return None
    row = pd.DataFrame([{name: features.get(name, np.nan) for name in FEATURE_COLUMNS}])
    return float(model.predict_proba(row)[0, 1])
