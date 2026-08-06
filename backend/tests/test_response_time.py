import pytest

from app.learner_model.response_time import update_response_time_statistics
from app.models.learner_state import LearnerConceptState


def _state() -> LearnerConceptState:
    return LearnerConceptState(learner_id="learner", concept_id="concept")


def test_response_time_welford_first_stable_variable_and_clamped() -> None:
    state = _state()
    update_response_time_statistics(state, 2000, 5.0)
    assert (state.response_time_count, state.average_response_time, state.response_time_m2) == (
        1,
        2.0,
        0.0,
    )
    assert state.response_time_variation == 0.0
    for milliseconds in (2000, 2000, 2000):
        update_response_time_statistics(state, milliseconds, 5.0)
    assert state.response_time_variation == 0.0
    variable = _state()
    for milliseconds in (1000, 3000, 5000):
        update_response_time_statistics(variable, milliseconds, 5.0)
    assert variable.average_response_time == 3.0
    assert variable.response_time_m2 == 8.0
    assert variable.response_time_variation == pytest.approx(0.4)
    update_response_time_statistics(variable, 1_000_000, 5.0)
    assert variable.response_time_variation == 1.0
