import pytest

from app.assessment.answer_evaluator import answers_equivalent


@pytest.mark.parametrize(
    ("submitted", "expected"),
    [
        ("2/4", "1/2"),
        ("0.5", "1/2"),
        ("1 1/2", "3/2"),
        ("-1 1/2", "-3/2"),
        ("5.0", "5"),
        (" 2 / 4 ", "1/2"),
        ("1⁄2", "2/4"),
        ("+1/2", "0.5"),
    ],
)
def test_numeric_answer_equivalence(submitted: str, expected: str) -> None:
    assert answers_equivalent(submitted, expected)


def test_invalid_and_text_answers_are_safe() -> None:
    assert not answers_equivalent("1/0", "1/2")
    assert answers_equivalent(" YES ", "yes")


@pytest.mark.parametrize("answer_type", ["integer", "number", "numeric", "fraction", "decimal"])
def test_numeric_types_reject_malformed_values(answer_type: str) -> None:
    assert not answers_equivalent("1/0", "1/2", answer_type)
    assert not answers_equivalent("1//2", "1//2", answer_type)
    assert not answers_equivalent("", "", answer_type)


def test_text_types_preserve_option_label_semantics() -> None:
    assert answers_equivalent(" 5 ", "5", "multiple_choice")
    assert answers_equivalent("Option A", "option a", "label")
    assert not answers_equivalent("1/2", "0.5", "choice")


def test_missing_answer_type_uses_numeric_only_when_both_values_parse() -> None:
    assert answers_equivalent("2/4", "0.5")
    assert answers_equivalent(" Answer ", "answer")
    assert not answers_equivalent("1/0", "1/2")
