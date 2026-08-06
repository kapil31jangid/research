import numpy as np

from app.evaluation.educational_metrics import (
    learning_gain,
    normalised_learning_gain,
    time_to_mastery,
)
from app.evaluation.resource_metrics import personalisation_retention_ratio
from app.evaluation.system_metrics import graceful_degradation, latency_summary


def test_evaluation_metrics_handle_expected_and_empty_inputs() -> None:
    pre = np.array([0.2, 0.4])
    post = np.array([0.4, 0.7])
    assert learning_gain(pre, post) > 0
    assert normalised_learning_gain(pre, post) > 0
    assert time_to_mastery(np.array([0.2, 0.8])) == 2
    assert latency_summary(np.array([1.0, 3.0]))["p95_ms"] >= 1
    assert personalisation_retention_ratio(0.5, 1) == 0.5
    assert graceful_degradation(1, 0.8) == 0.8
