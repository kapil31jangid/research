"""Resolve whether client-reported cached curriculum content is relevant."""

import json
from dataclasses import dataclass

from app.models.concept import Concept
from app.schemas.interactions import OfflineContentRequest


@dataclass(frozen=True)
class OfflineAvailability:
    available: bool
    matching_activity_ids: list[str]
    reason: str
    app_shell_available: bool


def resolve_offline_availability(
    request: OfflineContentRequest | None,
    concepts: list[Concept],
    target_concept_id: str,
    adaptation_path: str = "cached_offline_recommendation",
    misconception_id: str | None = None,
) -> OfflineAvailability:
    """Validate cached IDs against the seeded curriculum, not merely their presence."""
    app_shell_available = request.app_shell_available if request else False
    if request is None:
        return OfflineAvailability(
            False, [], "No offline metadata was supplied", app_shell_available
        )
    concept_by_activity = {
        activity_id: concept.id
        for concept in concepts
        for activity_id in json.loads(concept.activity_ids)
    }
    matching = [
        activity_id
        for activity_id in request.cached_activity_ids
        if concept_by_activity.get(activity_id) == target_concept_id
    ]
    if matching:
        return OfflineAvailability(
            True, matching, "Relevant cached activity is available", app_shell_available
        )
    if target_concept_id in request.cached_concept_ids:
        concept = next((item for item in concepts if item.id == target_concept_id), None)
        if concept and json.loads(concept.activity_ids):
            return OfflineAvailability(
                True,
                json.loads(concept.activity_ids),
                "Bundled content is available for the cached concept",
                app_shell_available,
            )
    reason = (
        "App shell is cached but no educational content matches"
        if app_shell_available
        else "No relevant cached educational content"
    )
    return OfflineAvailability(False, [], reason, app_shell_available)
