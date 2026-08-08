"""Load versioned curriculum seed files."""

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = PROJECT_ROOT / "data"


def load_json(relative_path: str) -> list[dict[str, Any]]:
    """Read a JSON list from the repository data directory."""
    with (DATA_ROOT / relative_path).open(encoding="utf-8") as source:
        content = json.load(source)
    if not isinstance(content, list):
        raise ValueError(f"Expected a list in {relative_path}")
    return content


def load_concepts() -> list[dict[str, Any]]:
    return load_json("curriculum/fractions.json")


def load_questions() -> list[dict[str, Any]]:
    return load_json("questions/fractions.json")


def load_activities() -> list[dict[str, Any]]:
    """Produce explicit metadata for every versioned legacy curriculum activity ID."""
    remediation = {
        "visual_common_denominator_demo": "adds_denominators",
        "fraction_bar_subtract": "subtracts_denominators",
        "fraction_number_line": "larger_denominator_larger_fraction",
        "equivalence_strip": "fails_equivalence",
        "denominator_ladder": "incorrect_common_denominator",
        "label_fraction_parts": "confuses_numerator_denominator",
        "conversion_steps": "mixed_improper_conversion",
        "simplify_with_tiles": "incorrect_cancelling",
    }
    activities: list[dict[str, Any]] = []
    for concept in load_concepts():
        for activity_id in concept["activity_ids"]:
            misconception_id = remediation.get(activity_id)
            paths = [
                "diagnostic_assessment",
                "prerequisite_review",
                "spaced_review",
                "rule_based_recommendation",
                "bkt_based_recommendation",
                "lightweight_ml_recommendation",
                "cached_offline_recommendation",
            ]
            activity_type = "practice_quiz"
            if misconception_id:
                paths.append("misconception_remediation")
                activity_type = "misconception_remediation"
            activities.append(
                {
                    "id": activity_id,
                    "concept_id": concept["id"],
                    "title": activity_id.replace("_", " ").title(),
                    "description": concept["description"],
                    "activity_type": activity_type,
                    "difficulty": concept["difficulty"],
                    "available_offline": True,
                    "bundled_locally": True,
                    "adaptation_paths": paths,
                    "misconception_ids": [misconception_id] if misconception_id else [],
                    "local_asset_key": activity_id,
                    "content_type": "lesson",
                    "estimated_size_kb": 64,
                    "estimated_computational_cost_ms": 1.0,
                    "is_active": True,
                    "deprecated_at": None,
                    "deprecation_reason": None,
                }
            )
    return activities
