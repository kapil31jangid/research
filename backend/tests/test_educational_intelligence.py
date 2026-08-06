from datetime import UTC, datetime, timedelta

import pytest

from app.curriculum.graph import build_graph, descendants, prerequisite_ids
from app.curriculum.loader import load_concepts
from app.curriculum.prerequisites import prerequisite_status
from app.misconceptions.detector import InteractionEvidence, detect_misconceptions
from app.misconceptions.rules import MisconceptionRule, load_rules
from app.core.config import Settings


def test_prerequisite_graph_helpers_and_mastery_gate() -> None:
    graph = build_graph(load_concepts())
    assert prerequisite_ids(graph, "fraction_addition") == ["common_denominators"]
    assert "fraction_word_problems" in descendants(graph, "fraction_addition")
    status = prerequisite_status(
        graph,
        "fraction_addition",
        {"common_denominators": 0.5},
        {"common_denominators": 0.75},
    )
    assert not status.eligible
    assert status.blocked_prerequisites == ["common_denominators"]


def test_misconception_detector_requires_repeated_matching_evidence() -> None:
    now = datetime.now(UTC)
    one_error = [InteractionEvidence("fraction_addition", False, ["adds_denominators"], now)]
    assert detect_misconceptions(one_error, load_rules()) == []
    repeated_errors = one_error + [
        InteractionEvidence(
            "fraction_addition", False, ["adds_denominators"], now - timedelta(minutes=1)
        )
    ]
    detection = detect_misconceptions(repeated_errors, load_rules())[0]
    assert detection.id == "adds_denominators"
    assert detection.evidence_count == 2
    assert detection.remediation_activity == "visual_common_denominator_demo"


def _rule(**overrides: object) -> MisconceptionRule:
    return MisconceptionRule(
        id="test_rule",
        concept_ids=["fraction_addition"],
        pattern_labels=["adds_denominators"],
        explanation="Test explanation",
        remediation_activity="test_remediation",
        **overrides,
    )


def _errors(count: int, concept_id: str = "fraction_addition") -> list[InteractionEvidence]:
    now = datetime.now(UTC)
    return [
        InteractionEvidence(concept_id, False, ["adds_denominators"], now - timedelta(minutes=index))
        for index in range(count)
    ]


def test_misconception_uses_global_defaults_when_rule_values_are_absent() -> None:
    settings = Settings(
        misconception_evidence_window=3,
        misconception_minimum_evidence=3,
        misconception_default_threshold=0.7,
    )
    assert detect_misconceptions(_errors(2), [_rule()], settings) == []
    detection = detect_misconceptions(_errors(3), [_rule()], settings)[0]
    assert detection.evidence_count == 3
    assert detection.confidence >= 0.7


def test_rule_values_override_global_misconception_configuration() -> None:
    settings = Settings(
        misconception_evidence_window=5,
        misconception_minimum_evidence=3,
        misconception_default_threshold=0.9,
    )
    rule = _rule(minimum_evidence=2, confidence_threshold=0.7, recent_window=2)
    detection = detect_misconceptions(_errors(3), [rule], settings)[0]
    assert detection.evidence_count == 2
    assert detection.confidence == pytest.approx(0.7)


def test_misconception_ignores_unrelated_patterns_and_concepts() -> None:
    evidence = _errors(2, "fraction_subtraction") + [
        InteractionEvidence("fraction_addition", False, ["other_pattern"], datetime.now(UTC))
    ]
    assert detect_misconceptions(evidence, [_rule()]) == []
