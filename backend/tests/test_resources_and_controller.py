from app.controller.explanation import explain_decision
from app.controller.policy import ControllerInput, decide_adaptation
from app.resources.scoring import (
    ResourceSnapshot,
    calculate_resource_score,
    classify_resource_level,
)


def snapshot(level_score: float, level: str) -> ResourceSnapshot:
    return ResourceSnapshot(
        available_memory_mb=500,
        total_memory_mb=1_000,
        cpu_percent=30,
        battery_percent=50,
        battery_charging=None,
        network_available=True,
        network_quality=1.0,
        offline=False,
        storage_available_mb=1_000,
        inference_latency_ms=1,
        score=level_score,
        level=level,  # type: ignore[arg-type]
    )


def test_resource_scoring_and_classification() -> None:
    constrained = calculate_resource_score(100, 1_000, 90, 10, False, 0.0)
    capable = calculate_resource_score(900, 1_000, 10, 90, True, 1.0)
    assert constrained < capable
    assert classify_resource_level(0.2) == "critical"
    assert classify_resource_level(0.9) == "high"


def test_controller_uses_priority_order_and_explains_rejections() -> None:
    state = ControllerInput(
        misconception_confidence=0.8,
        prerequisite_mastery=0.4,
        uncertainty=0.9,
        retained_mastery=0.2,
        interaction_count=40,
        resource=snapshot(0.9, "high"),
    )
    decision = decide_adaptation(state)
    assert decision.adaptation_path == "misconception_remediation"
    assert "prerequisite_review" in decision.rejected_paths
    assert "high-confidence misconception" in explain_decision(decision, state)[0]


def test_controller_degrades_to_cached_content_under_critical_resources() -> None:
    state = ControllerInput(
        misconception_confidence=0.0,
        prerequisite_mastery=1.0,
        uncertainty=0.1,
        retained_mastery=1.0,
        interaction_count=1,
        resource=snapshot(0.1, "critical"),
        offline_cache_available=True,
    )
    assert decide_adaptation(state).adaptation_path == "cached_offline_recommendation"


def test_controller_falls_back_to_bkt_when_ml_artifact_is_unavailable() -> None:
    state = ControllerInput(0.0, 1.0, 0.1, 1.0, 40, snapshot(0.9, "high"))
    assert decide_adaptation(state).adaptation_path == "bkt_based_recommendation"
