from app.models.concept import Concept
from app.offline.content_availability import resolve_offline_availability
from app.schemas.interactions import OfflineContentRequest


def _concepts() -> list[Concept]:
    return [
        Concept(
            id="target",
            name="Target",
            description="",
            difficulty=1,
            activity_ids='["target_activity"]',
        ),
        Concept(
            id="other",
            name="Other",
            description="",
            difficulty=1,
            activity_ids='["other_activity"]',
        ),
    ]


def test_offline_resolver_requires_relevant_educational_content() -> None:
    concepts = _concepts()
    assert resolve_offline_availability(None, concepts, "target").available is False
    assert (
        resolve_offline_availability(
            OfflineContentRequest(app_shell_available=True), concepts, "target"
        ).available
        is False
    )
    assert (
        resolve_offline_availability(
            OfflineContentRequest(cached_activity_ids=["other_activity"]), concepts, "target"
        ).available
        is False
    )
    availability = resolve_offline_availability(
        OfflineContentRequest(cached_activity_ids=["target_activity"]), concepts, "target"
    )
    assert availability.available
    assert availability.matching_activity_ids == ["target_activity"]


def test_offline_resolver_accepts_seeded_concept_content_without_app_shell() -> None:
    availability = resolve_offline_availability(
        OfflineContentRequest(cached_concept_ids=["target"]), _concepts(), "target"
    )
    assert availability.available
    assert availability.app_shell_available is False
