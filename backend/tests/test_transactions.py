import json

import pytest
from sqlalchemy import select

from app.controller.policy import ControllerDecision
from app.ml_runtime.exceptions import ResponsePredictionError
from app.models.interaction import Interaction
from app.models.learner_state import LearnerConceptState, MasteryHistory
from app.models.recommendation import Recommendation


def _learner(client):
    return client(
        "POST", "/learners", json={"name": "Txn", "age_group": "10-12", "grade": 5}
    ).json()


def _payload(learner_id: str) -> dict[str, object]:
    return {
        "learner_id": learner_id,
        "question_id": "whole_numbers_01",
        "submitted_answer": "19",
        "response_time_ms": 1000,
    }


def test_interaction_persists_atomically_in_a_fresh_session(client) -> None:
    learner = _learner(client)
    response = client("POST", "/interactions", json=_payload(learner["id"]))
    assert response.status_code == 201
    with client.session_factory() as db:
        state = db.scalar(
            select(LearnerConceptState).where(
                LearnerConceptState.learner_id == learner["id"],
                LearnerConceptState.concept_id == "whole_numbers",
            )
        )
        recommendation = db.scalar(
            select(Recommendation).where(Recommendation.learner_id == learner["id"])
        )
        assert (
            db.scalar(select(Interaction).where(Interaction.learner_id == learner["id"]))
            is not None
        )
        assert (
            db.scalar(select(MasteryHistory).where(MasteryHistory.learner_id == learner["id"]))
            is not None
        )
        assert state is not None and state.attempts >= 1
        assert recommendation is not None and recommendation.measured_total_adaptive_latency_ms >= 0
        assert json.loads(recommendation.matching_offline_activity_ids) == []
        assert recommendation.offline_content_reason == "No offline metadata was supplied"


def test_late_recommendation_failure_rolls_back_everything(client, monkeypatch) -> None:
    learner = _learner(client)
    monkeypatch.setattr(
        "app.services.interaction_service.generate_recommendation",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("late failure")),
    )
    with pytest.raises(RuntimeError, match="late failure"):
        client("POST", "/interactions", json=_payload(learner["id"]))
    with client.session_factory() as db:
        assert db.scalar(select(Interaction).where(Interaction.learner_id == learner["id"])) is None
        assert (
            db.scalar(select(Recommendation).where(Recommendation.learner_id == learner["id"]))
            is None
        )
        assert (
            db.scalar(select(MasteryHistory).where(MasteryHistory.learner_id == learner["id"]))
            is None
        )


def test_ml_prediction_failure_falls_back_and_commits(client, monkeypatch) -> None:
    learner = _learner(client)
    decision = ControllerDecision(
        adaptation_path="lightweight_ml_recommendation",
        reason="test ML path",
        triggered_rules=["test"],
        rejected_paths=[],
        estimated_computational_cost_ms=8.0,
        decision_confidence=1.0,
        resource_score=1.0,
    )
    monkeypatch.setattr("app.services.interaction_service.decide_adaptation", lambda _: decision)
    from app.services import interaction_service

    original = interaction_service.generate_recommendation
    calls = 0

    def fail_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ResponsePredictionError("candidate schema validation failed")
        return original(*args, **kwargs)

    monkeypatch.setattr("app.services.interaction_service.generate_recommendation", fail_once)
    response = client("POST", "/interactions", json=_payload(learner["id"]))
    assert response.status_code == 201
    recommendation = response.json()["decision"]
    assert recommendation["requested_adaptation_path"] == "lightweight_ml_recommendation"
    assert recommendation["adaptation_path"] == "bkt_based_recommendation"
    assert recommendation["fallback_used"] is True
    assert "candidate schema validation failed" in recommendation["fallback_reason"]
    with client.session_factory() as db:
        assert db.scalar(select(Interaction).where(Interaction.learner_id == learner["id"]))
        persisted = db.scalar(
            select(Recommendation).where(Recommendation.learner_id == learner["id"])
        )
        assert persisted is not None and persisted.fallback_used is True
        assert persisted.selected_candidate_predicted_probability is None
        assert json.loads(persisted.candidate_prediction_summary) == []


def test_prerequisite_review_targets_the_weakest_direct_prerequisite(client, monkeypatch) -> None:
    learner = _learner(client)
    decision = ControllerDecision(
        adaptation_path="prerequisite_review",
        reason="test prerequisite path",
        triggered_rules=["test"],
        rejected_paths=[],
        estimated_computational_cost_ms=1.5,
        decision_confidence=1.0,
        resource_score=1.0,
    )
    monkeypatch.setattr("app.services.interaction_service.decide_adaptation", lambda _: decision)
    payload = _payload(learner["id"])
    payload["question_id"] = "fraction_addition_01"
    payload["submitted_answer"] = "3/8"
    response = client("POST", "/interactions", json=payload)
    assert response.status_code == 201
    assert response.json()["decision"]["selected_concept_id"] == "common_denominators"
