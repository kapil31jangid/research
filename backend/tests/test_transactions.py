import pytest
from sqlalchemy import select

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
