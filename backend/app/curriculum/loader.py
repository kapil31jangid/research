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
    from app.curriculum.registry import chapter_for_concept

    concepts = load_json("curriculum/fractions.json") + load_json(
        "curriculum/ncert/class_6/mathematics/concepts.json"
    )
    for concept in concepts:
        chapter = chapter_for_concept(concept["id"])
        if chapter is None:
            raise ValueError(f"Concept {concept['id']} is missing a curriculum chapter")
        concept["chapter_id"] = chapter.id
    return concepts


def load_questions() -> list[dict[str, Any]]:
    return load_json("questions/fractions.json") + load_json(
        "questions/ncert/class_6/mathematics/questions.json"
    )


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
    from app.curriculum.registry import get_curriculum_context

    activities: list[dict[str, Any]] = []
    for concept in load_concepts():
        context = get_curriculum_context(concept["id"], concept["name"])
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
                    "content_origin": "original_adaptive_material",
                    "aligned_board": context.board_id,
                    "official_reference_url": "https://ncert.nic.in/textbook.php",
                    "curriculum_pack_id": context.curriculum_pack_id,
                    "curriculum_pack_version": context.curriculum_pack_version,
                    "is_active": True,
                    "deprecated_at": None,
                    "deprecation_reason": None,
                }
            )
    return activities
