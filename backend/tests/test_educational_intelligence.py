from datetime import UTC, datetime, timedelta

from app.curriculum.graph import build_graph, descendants, prerequisite_ids
from app.curriculum.loader import load_concepts
from app.curriculum.prerequisites import prerequisite_status
from app.misconceptions.detector import InteractionEvidence, detect_misconceptions
from app.misconceptions.rules import load_rules


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
