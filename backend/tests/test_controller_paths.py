import pytest

from app.controller.policy import ControllerInput, decide_adaptation
from app.resources.scoring import ResourceSnapshot


def _resource(level: str) -> ResourceSnapshot:
    score = {"critical": 0.1, "low": 0.4, "moderate": 0.6, "high": 0.9}[level]
    return ResourceSnapshot(1, 1, 0, 100, False, True, 1, False, 100, 0, score, level)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("resource", "kwargs", "expected"),
    [
        ("high", {"uncertainty": 0.9}, "diagnostic_assessment"),
        ("high", {"prerequisite_mastery": 0.1}, "prerequisite_review"),
        ("low", {"misconception_confidence": 0.9}, "misconception_remediation"),
        ("moderate", {"retained_mastery": 0.1}, "spaced_review"),
        ("critical", {"offline_cache_available": True}, "cached_offline_recommendation"),
        ("critical", {}, "rule_based_recommendation"),
        ("low", {}, "rule_based_recommendation"),
        ("moderate", {}, "bkt_based_recommendation"),
        (
            "high",
            {"interaction_count": 30, "ml_model_available": True},
            "lightweight_ml_recommendation",
        ),
    ],
)
def test_every_controller_path_is_reachable(
    resource: str, kwargs: dict[str, object], expected: str
) -> None:
    values: dict[str, object] = dict(
        misconception_confidence=0.0,
        prerequisite_mastery=1.0,
        uncertainty=0.1,
        retained_mastery=1.0,
        interaction_count=0,
        resource=_resource(resource),
    )
    values.update(kwargs)
    assert decide_adaptation(ControllerInput(**values)).adaptation_path == expected
