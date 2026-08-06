from app.models.activity import LearningActivity
from app.offline.content_availability import resolve_offline_availability
from app.schemas.interactions import OfflineContentRequest


def _activities() -> list[LearningActivity]:
    return [
        LearningActivity(
            id="target",
            concept_id="target",
            title="Target",
            description="",
            difficulty=1,
            activity_type="practice_quiz",
            available_offline=True,
            bundled_locally=True,
            adaptation_paths='["cached_offline_recommendation"]',
            misconception_ids="[]",
        ),
        LearningActivity(
            id="other",
            concept_id="other",
            title="Other",
            description="",
            difficulty=1,
            activity_type="practice_quiz",
            available_offline=True,
            bundled_locally=True,
            adaptation_paths='["cached_offline_recommendation"]',
            misconception_ids="[]",
        ),
    ]


def test_offline_resolver_requires_relevant_educational_content() -> None:
    activities = _activities()
    assert resolve_offline_availability(None, activities, "target").available is False
    assert (
        resolve_offline_availability(
            OfflineContentRequest(app_shell_available=True), activities, "target"
        ).available
        is False
    )
    assert (
        resolve_offline_availability(
            OfflineContentRequest(cached_activity_ids=["other"]), activities, "target"
        ).available
        is False
    )
    availability = resolve_offline_availability(
        OfflineContentRequest(cached_activity_ids=["target"]), activities, "target"
    )
    assert availability.available
    assert availability.matching_activity_ids == ["target"]


def test_offline_resolver_accepts_seeded_concept_content_without_app_shell() -> None:
    availability = resolve_offline_availability(
        OfflineContentRequest(cached_concept_ids=["target"]), _activities(), "target"
    )
    assert availability.available
    assert availability.app_shell_available is False
