"""Deterministic loader and integrity checks for learner-facing activity content."""

import json
from functools import lru_cache
from typing import Any

from pydantic import ValidationError

from app.curriculum.loader import DATA_ROOT, load_activities, load_concepts
from app.schemas.activity_content import ActivityContent

CONTENT_ROOT = DATA_ROOT / "activities" / "fractions"


@lru_cache(maxsize=1)
def _content_index() -> dict[str, ActivityContent]:
    documents: dict[str, ActivityContent] = {}
    for path in sorted(CONTENT_ROOT.glob("*.json")):
        with path.open(encoding="utf-8") as source:
            raw: Any = json.load(source)
        if not isinstance(raw, list):
            raise ValueError(f"Activity content file must contain a list: {path.name}")
        for item in raw:
            try:
                content = ActivityContent.model_validate(item)
            except ValidationError as error:
                raise ValueError(f"Invalid activity content in {path.name}: {error}") from error
            if content.id in documents:
                raise ValueError(f"Duplicate activity content ID: {content.id}")
            documents[content.id] = content
    return documents


def load_all_activity_content() -> tuple[ActivityContent, ...]:
    """Return validated content in stable ID order."""
    return tuple(_content_index()[item] for item in sorted(_content_index()))


def load_activity_content(activity_id: str) -> ActivityContent | None:
    return _content_index().get(activity_id)


def load_content_for_concept(concept_id: str) -> tuple[ActivityContent, ...]:
    return tuple(
        content for content in load_all_activity_content() if content.concept_id == concept_id
    )


def validate_activity_content(
    *,
    activities: list[dict[str, Any]] | None = None,
    concepts: list[dict[str, Any]] | None = None,
) -> None:
    """Fail fast when active activity metadata and content documents diverge."""
    activity_rows = activities if activities is not None else load_activities()
    concept_rows = concepts if concepts is not None else load_concepts()
    content_rows = load_all_activity_content()
    activities_by_id = {row["id"]: row for row in activity_rows}
    concept_ids = {row["id"] for row in concept_rows}
    content_ids = {row.id for row in content_rows}

    for content in content_rows:
        activity = activities_by_id.get(content.id)
        if activity is None:
            raise ValueError(f"Content {content.id} references an unknown activity")
        if content.concept_id not in concept_ids:
            raise ValueError(
                f"Content {content.id} references unknown concept {content.concept_id}"
            )
        if content.concept_id != activity["concept_id"]:
            raise ValueError(f"Content {content.id} does not match its activity concept")
        if not activity.get("is_active", True) or activity.get("deprecated_at") is not None:
            raise ValueError(f"Inactive activity {content.id} must not have active learner content")
        if content.offline_ready and not activity.get("available_offline", False):
            raise ValueError(f"Content {content.id} claims unsupported offline availability")

    missing = {
        row["id"]
        for row in activity_rows
        if row.get("is_active", True) and row.get("deprecated_at") is None
    } - content_ids
    if missing:
        raise ValueError(f"Active activities missing learner content: {sorted(missing)}")


def clear_activity_content_cache() -> None:
    """Clear the immutable document cache for isolated tests."""
    _content_index.cache_clear()
