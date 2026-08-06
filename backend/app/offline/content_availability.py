"""Resolve whether client-reported cached curriculum content is relevant."""

import json
from dataclasses import dataclass

from app.models.activity import LearningActivity
from app.schemas.interactions import OfflineContentRequest


@dataclass(frozen=True)
class OfflineAvailability:
    available: bool
    matching_activity_ids: list[str]
    reason: str
    app_shell_available: bool
    adaptation_path: str
    misconception_id: str | None


def resolve_offline_availability(
    request: OfflineContentRequest | None,
    activities: list[LearningActivity],
    target_concept_id: str,
    adaptation_path: str = "cached_offline_recommendation",
    misconception_id: str | None = None,
) -> OfflineAvailability:
    """Validate cached educational content against activity metadata."""
    app_shell_available = request.app_shell_available if request else False
    if request is None:
        return OfflineAvailability(
            False,
            [],
            "No offline metadata was supplied",
            app_shell_available,
            adaptation_path,
            misconception_id,
        )
    cached_ids = set(request.cached_activity_ids)
    matching = []
    for activity in activities:
        paths = set(json.loads(activity.adaptation_paths))
        misconceptions = set(json.loads(activity.misconception_ids))
        explicitly_cached = activity.id in cached_ids
        concept_cached_and_bundled = (
            activity.concept_id in request.cached_concept_ids and activity.bundled_locally
        )
        if not (explicitly_cached or concept_cached_and_bundled):
            continue
        if not (activity.concept_id == target_concept_id and activity.available_offline):
            continue
        if adaptation_path not in paths and "cached_offline_recommendation" not in paths:
            continue
        if (
            adaptation_path == "misconception_remediation"
            and misconception_id not in misconceptions
        ):
            continue
        matching.append(activity.id)
    if matching:
        return OfflineAvailability(
            True,
            matching,
            "Relevant cached activity is available",
            app_shell_available,
            adaptation_path,
            misconception_id,
        )
    reason = (
        "App shell is cached but no educational content matches"
        if app_shell_available
        else "No relevant cached educational content"
    )
    return OfflineAvailability(
        False, [], reason, app_shell_available, adaptation_path, misconception_id
    )
