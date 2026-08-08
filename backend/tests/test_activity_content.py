"""Learner-facing curriculum content integrity and API coverage."""

import json
from collections.abc import Callable, Iterator
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum import content_loader
from app.curriculum.content_loader import (
    clear_activity_content_cache,
    load_activity_content,
    load_all_activity_content,
    load_content_for_concept,
    validate_activity_content,
)
from app.curriculum.loader import load_activities, load_concepts
from app.database.seed import seed_database
from app.models.activity import LearningActivity


@pytest.fixture(autouse=True)
def clear_content_cache() -> Iterator[None]:
    clear_activity_content_cache()
    yield
    clear_activity_content_cache()


def test_every_active_activity_has_rich_valid_content() -> None:
    activities = load_activities()
    documents = load_all_activity_content()

    assert {item.id for item in documents} == {item["id"] for item in activities}
    assert all(item.learning_objective for item in documents)
    assert all(len(item.sections) >= 5 for item in documents)
    assert all(item.offline_ready for item in documents)
    validate_activity_content()


def test_content_lookup_is_stable_and_concept_scoped() -> None:
    first = load_activity_content("visual_common_denominator_demo")
    second = load_activity_content("visual_common_denominator_demo")
    fraction_addition = load_content_for_concept("fraction_addition")

    assert first is second
    assert first is not None
    assert first.concept_id == "fraction_addition"
    assert {item.id for item in fraction_addition} == {
        "visual_common_denominator_demo",
        "addition_steps",
    }


def test_duplicate_content_ids_fail_fast(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    content = load_all_activity_content()[0].model_dump(mode="json")
    (tmp_path / "one.json").write_text(json.dumps([content]), encoding="utf-8")
    (tmp_path / "two.json").write_text(json.dumps([content]), encoding="utf-8")
    monkeypatch.setattr(content_loader, "CONTENT_ROOT", tmp_path)
    clear_activity_content_cache()

    with pytest.raises(ValueError, match="Duplicate activity content ID"):
        load_all_activity_content()


def test_invalid_section_type_fails_fast(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    content = load_all_activity_content()[0].model_dump(mode="json")
    content["sections"][0]["type"] = "video_magic"
    (tmp_path / "invalid.json").write_text(json.dumps([content]), encoding="utf-8")
    monkeypatch.setattr(content_loader, "CONTENT_ROOT", tmp_path)
    clear_activity_content_cache()

    with pytest.raises(ValueError, match="Invalid activity content"):
        load_all_activity_content()


def test_unknown_activity_content_fails_integrity_validation() -> None:
    activities = [item for item in load_activities() if item["id"] != "number_line_walk"]
    with pytest.raises(ValueError, match="unknown activity"):
        validate_activity_content(activities=activities, concepts=load_concepts())


def test_inactive_content_mismatch_fails_integrity_validation() -> None:
    activities = load_activities()
    activities[0] = {**activities[0], "is_active": False}
    with pytest.raises(ValueError, match="Inactive activity"):
        validate_activity_content(activities=activities, concepts=load_concepts())


def test_activity_content_api_is_learner_safe(client: Callable[..., httpx.Response]) -> None:
    response = client("GET", "/activities/visual_common_denominator_demo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["activity"]["concept_id"] == "fraction_addition"
    assert payload["activity"]["available_offline"] is True
    assert payload["content"]["learning_objective"]
    assert len(payload["content"]["sections"]) >= 5
    assert "adaptation_paths" not in payload["activity"]
    assert "misconception_ids" not in payload["activity"]


def test_concept_activity_api_and_missing_content(
    client: Callable[..., httpx.Response],
) -> None:
    response = client("GET", "/concepts/fraction_addition/activities")
    missing = client("GET", "/activities/not_real")

    assert response.status_code == 200
    assert {item["activity"]["id"] for item in response.json()} == {
        "visual_common_denominator_demo",
        "addition_steps",
    }
    assert missing.status_code == 404


def test_seed_reconciles_stale_activity_metadata_without_reactivating(
    client: Callable[..., httpx.Response],
) -> None:
    factory = client.session_factory  # type: ignore[attr-defined]
    with factory() as db:
        db: Session
        activity = db.scalar(
            select(LearningActivity).where(LearningActivity.id == "number_line_walk")
        )
        assert activity is not None
        activity.adaptation_paths = '["rule_based_recommendation"]'
        activity.is_active = False
        db.commit()
        seed_database(db)
    with factory() as fresh:
        activity = fresh.get(LearningActivity, "number_line_walk")
        assert activity is not None
        assert "diagnostic_assessment" in json.loads(activity.adaptation_paths)
        assert activity.is_active is False
