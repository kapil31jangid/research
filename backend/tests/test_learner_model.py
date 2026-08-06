from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.learner_model.bkt import BKTParameters, update_mastery
from app.learner_model.forgetting import retained_mastery, update_forgetting_rate
from app.learner_model.state import parameters_for_concept
from app.learner_model.uncertainty import (
    calculate_uncertainty,
    entropy_uncertainty,
    heuristic_uncertainty,
    response_time_variation,
)


def test_bkt_correct_response_increases_mastery() -> None:
    parameters = BKTParameters(
        learning_probability=0.1, slip_probability=0.1, guess_probability=0.2
    )
    assert update_mastery(0.3, correct=True, parameters=parameters) > 0.3


def test_bkt_incorrect_response_reduces_mastery_before_learning_transition() -> None:
    parameters = BKTParameters(
        learning_probability=0.0, slip_probability=0.1, guess_probability=0.2
    )
    assert update_mastery(0.7, correct=False, parameters=parameters) < 0.7


def test_bkt_parameters_reject_invalid_probabilities() -> None:
    with pytest.raises(ValidationError):
        BKTParameters(guess_probability=1.1)


def test_bkt_supports_concept_specific_parameters() -> None:
    addition = parameters_for_concept("fraction_addition", difficulty=3)
    subtraction = parameters_for_concept("fraction_subtraction", difficulty=3)
    assert addition != subtraction


def test_uncertainty_modes_and_response_time_normalisation() -> None:
    variation = response_time_variation([1.0, 3.0])
    assert 0.0 < variation <= 1.0
    heuristic = heuristic_uncertainty(3, [True, False, True], variation)
    assert calculate_uncertainty("heuristic", 0.5, 3, [True, False, True], variation) == heuristic
    assert entropy_uncertainty(0.5) == 1.0
    assert calculate_uncertainty("combined", 0.5, 3, [True], 0.0) <= 1.0


def test_forgetting_is_dynamic_and_rate_can_be_updated() -> None:
    two_days_ago = datetime.now(UTC) - timedelta(days=2)
    assert retained_mastery(0.8, two_days_ago, 0.1) < 0.8
    assert retained_mastery(0.8, None, 0.1) == 0.8
    assert update_forgetting_rate(0.03, delayed_review_correct=False) > 0.03
    assert update_forgetting_rate(0.03, delayed_review_correct=True) < 0.03
