"""Educational metrics with explicit zero-denominator handling."""

import numpy as np


def accuracy(correct: np.ndarray) -> float:
    return float(np.mean(correct)) if len(correct) else 0.0


def learning_gain(pre: np.ndarray, post: np.ndarray) -> float:
    return float(np.mean(post - pre)) if len(pre) else 0.0


def normalised_learning_gain(pre: np.ndarray, post: np.ndarray) -> float:
    denominator = np.maximum(1.0 - pre, 1e-9)
    return float(np.mean((post - pre) / denominator)) if len(pre) else 0.0


def retention_score(mastery: np.ndarray, retained: np.ndarray) -> float:
    denominator = np.maximum(mastery, 1e-9)
    return float(np.mean(retained / denominator)) if len(mastery) else 0.0


def time_to_mastery(mastery_history: np.ndarray, threshold: float = 0.75) -> int | None:
    reached = np.flatnonzero(mastery_history >= threshold)
    return int(reached[0] + 1) if len(reached) else None
