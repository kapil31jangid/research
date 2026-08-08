"""Regression coverage for the NCERT multi-class curriculum architecture."""

from pathlib import Path

from sqlalchemy import select

from app.curriculum.loader import load_activities, load_concepts, load_questions
from app.curriculum.registry import (
    CONTENT_ORIGIN,
    get_classes,
    get_curriculum_context,
    get_subjects,
    load_content_pack_manifests,
    validate_curriculum_registry,
)
from app.models.learner_state import LearnerConceptState


def _create_learner(client, class_level: int) -> dict[str, object]:
    response = client(
        "POST",
        "/learners",
        json={
            "name": f"Class {class_level} learner",
            "age_group": "synthetic-test",
            "grade": class_level,
            "class_level": class_level,
            "board_id": "ncert",
            "active_subject_id": f"ncert-c{class_level}-mathematics",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_registry_represents_classes_one_to_twelve_and_class_scoped_subjects():
    classes = get_classes("ncert")
    assert [item.class_level for item in classes] == list(range(1, 13))
    assert get_subjects("ncert", 5)[0].id == "ncert-c5-mathematics"
    assert get_subjects("ncert", 6)[0].id == "ncert-c6-mathematics"
    assert get_subjects("unknown", 5) == ()


def test_registry_manifests_and_original_content_are_valid():
    validate_curriculum_registry(
        concepts=load_concepts(), activities=load_activities(), questions=load_questions()
    )
    manifests = load_content_pack_manifests()
    assert {item.id for item in manifests} == {
        "ncert-class-5-mathematics",
        "ncert-class-6-mathematics",
    }
    assert all(item.content_origin == CONTENT_ORIGIN for item in manifests)
    assert all(activity["content_origin"] == CONTENT_ORIGIN for activity in load_activities())


def test_curriculum_discovery_relationships_and_context(client):
    classes = client("GET", "/curriculum/boards/ncert/classes").json()
    assert len(classes) == 12
    subjects = client("GET", "/curriculum/boards/ncert/classes/6/subjects").json()
    assert [item["name"] for item in subjects] == ["Mathematics"]
    books = client("GET", f"/curriculum/subjects/{subjects[0]['id']}/books").json()
    chapters = client("GET", f"/curriculum/books/{books[0]['id']}/chapters").json()
    assert [item["title"] for item in chapters] == ["Number Play", "Fractions"]
    context = client("GET", "/concepts/c6_fraction_operations/context").json()
    assert context["class_level"] == 6
    assert context["chapter_title"] == "Fractions"
    assert context["content_origin"] == CONTENT_ORIGIN


def test_class_six_question_and_recommendation_stay_in_scope(client):
    learner = _create_learner(client, 6)
    selection = client("GET", f"/questions/next?learner_id={learner['id']}")
    assert selection.status_code == 200
    selected = selection.json()
    assert selected["concept_id"].startswith("c6_")
    context = get_curriculum_context(selected["concept_id"])
    response = client(
        "POST",
        "/interactions",
        json={
            "learner_id": learner["id"],
            "question_id": selected["question"]["id"],
            "submitted_answer": selected["question"]["options"][0],
            "response_time_ms": 1200,
            "curriculum_context": {
                "board_id": context.board_id,
                "class_level": context.class_level,
                "subject_id": context.subject_id,
                "book_id": context.book_id,
                "chapter_id": context.chapter_id,
                "curriculum_pack_version": context.curriculum_pack_version,
            },
        },
    )
    assert response.status_code == 201, response.text
    decision_context = response.json()["decision"]["curriculum_context"]
    assert decision_context["subject_id"] in {
        "ncert-c6-mathematics",
        "ncert-c5-mathematics",  # Explicit prerequisite review bridge.
    }


def test_class_six_target_can_bridge_to_class_five_prerequisite(client):
    learner = _create_learner(client, 6)
    response = client(
        "POST",
        "/interactions",
        json={
            "learner_id": learner["id"],
            "question_id": "c6_number_patterns_01",
            "submitted_answer": "20",
            "response_time_ms": 800,
        },
    )
    assert response.status_code == 201, response.text
    decision = response.json()["decision"]
    assert decision["requested_adaptation_path"] == "prerequisite_review"
    assert decision["selected_concept_id"] == "whole_numbers"
    assert decision["curriculum_context"]["class_level"] == 5


def test_switching_class_preserves_existing_concept_state(client):
    learner = _create_learner(client, 5)
    factory = client.session_factory
    with factory() as db:
        state = db.scalar(
            select(LearnerConceptState).where(
                LearnerConceptState.learner_id == learner["id"],
                LearnerConceptState.concept_id == "fraction_meaning",
            )
        )
        if state is None:
            client("GET", f"/learners/{learner['id']}/state")
            state = db.scalar(
                select(LearnerConceptState).where(
                    LearnerConceptState.learner_id == learner["id"],
                    LearnerConceptState.concept_id == "fraction_meaning",
                )
            )
        assert state is not None
        state.mastery_probability = 0.73
        db.commit()
    switched = client(
        "PATCH",
        f"/learners/{learner['id']}/pathway",
        json={
            "board_id": "ncert",
            "class_level": 6,
            "subject_id": "ncert-c6-mathematics",
        },
    )
    assert switched.status_code == 200
    client("GET", f"/learners/{learner['id']}/state")
    with factory() as db:
        preserved = db.scalar(
            select(LearnerConceptState).where(
                LearnerConceptState.learner_id == learner["id"],
                LearnerConceptState.concept_id == "fraction_meaning",
            )
        )
        assert preserved is not None
        assert preserved.mastery_probability == 0.73


def test_unavailable_and_mismatched_pathways_fail_safely(client):
    unavailable = client(
        "POST",
        "/learners",
        json={
            "name": "Future learner",
            "age_group": "6-8",
            "grade": 2,
            "class_level": 2,
            "active_subject_id": "ncert-c2-mathematics",
        },
    )
    assert unavailable.status_code == 422
    learner = _create_learner(client, 6)
    mismatch = client(
        "POST",
        "/interactions",
        json={
            "learner_id": learner["id"],
            "question_id": "c6_number_patterns_01",
            "submitted_answer": "20",
            "response_time_ms": 900,
            "curriculum_context": {
                "board_id": "ncert",
                "class_level": 5,
                "subject_id": "ncert-c5-mathematics",
                "book_id": "ncert-c5-math-reference",
                "chapter_id": "ncert-c5-math-fractions",
                "curriculum_pack_version": "1.0.0",
            },
        },
    )
    assert mismatch.status_code == 422


def test_curriculum_data_uses_only_official_reference_host():
    for manifest in load_content_pack_manifests():
        assert "ncert.nic.in" in str(manifest.official_reference_url)
    assert Path("data/curriculum/ncert/registry.json").is_file()
