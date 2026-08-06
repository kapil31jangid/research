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
    ],
)
def test_numeric_answer_equivalence(submitted: str, expected: str) -> None:
    assert answers_equivalent(submitted, expected)


def test_invalid_and_text_answers_are_safe() -> None:
    assert not answers_equivalent("1/0", "1/2")
    assert answers_equivalent(" YES ", "yes")
