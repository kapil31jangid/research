"""Synthetic-only ML metrics with temporally aligned recommendation outcomes."""

import numpy as np
import pandas as pd


def matched_prediction_outcomes(interactions: pd.DataFrame) -> pd.DataFrame:
    matches: list[dict[str, float]] = []
    for _, group in interactions.groupby("synthetic_learner_id"):
        ordered = group.sort_values("step")
        for _position, row in ordered.iterrows():
            probability = row.selected_candidate_predicted_probability
            if pd.isna(probability):
                continue
            later = ordered.loc[
                (ordered.step > row.step) & (ordered.concept_id == row.selected_concept_id)
            ]
            if not later.empty:
                matches.append(
                    {
                        "probability": float(probability),
                        "outcome": float(bool(later.iloc[0].correct)),
                    }
                )
    return pd.DataFrame(matches, columns=["probability", "outcome"])


def synthetic_ml_metrics(interactions: pd.DataFrame) -> dict[str, float | int | None]:
    matched = matched_prediction_outcomes(interactions)
    if matched.empty:
        return {
            "synthetic_ml_matched_samples": 0,
            "synthetic_brier_score": None,
            "synthetic_log_loss": None,
            "synthetic_roc_auc": None,
            "synthetic_accuracy_at_0_5": None,
            "synthetic_expected_calibration_error": None,
        }
    probability = matched.probability.to_numpy(dtype=float)
    outcome = matched.outcome.to_numpy(dtype=float)
    clipped = np.clip(probability, 1e-12, 1 - 1e-12)
    roc_auc = None
    if len(np.unique(outcome)) == 2:
        positive = probability[outcome == 1]
        negative = probability[outcome == 0]
        roc_auc = float(
            np.mean(
                [
                    float(left > right) + 0.5 * float(left == right)
                    for left in positive
                    for right in negative
                ]
            )
        )
    calibration = 0.0
    bins = np.linspace(0, 1, 11)
    for lower, upper in zip(bins[:-1], bins[1:], strict=True):
        mask = (probability >= lower) & (
            (probability < upper) | ((upper == 1.0) & (probability <= upper))
        )
        if mask.any():
            calibration += float(mask.mean()) * abs(
                float(probability[mask].mean()) - float(outcome[mask].mean())
            )
    return {
        "synthetic_ml_matched_samples": int(len(matched)),
        "synthetic_brier_score": float(np.mean((probability - outcome) ** 2)),
        "synthetic_log_loss": float(
            -np.mean(outcome * np.log(clipped) + (1 - outcome) * np.log(1 - clipped))
        ),
        "synthetic_roc_auc": roc_auc,
        "synthetic_accuracy_at_0_5": float(np.mean((probability >= 0.5) == outcome.astype(bool))),
        "synthetic_expected_calibration_error": calibration,
    }
