"""Deterministic mathematical answer equivalence without expression evaluation."""

import re
from fractions import Fraction

_MIXED = re.compile(r"^([+-]?\d+)\s+(\d+)\s*/\s*(\d+)$")
_NUMERIC_TYPES = {"integer", "number", "numeric", "fraction", "decimal", "mixed_number"}
_TEXT_TYPES = {"text", "short_text", "multiple_choice", "choice", "label"}


def _fraction(value: str) -> Fraction | None:
    text = value.strip().replace("⁄", "/")
    match = _MIXED.fullmatch(text)
    try:
        if match:
            whole, numerator, denominator = map(int, match.groups())
            if denominator == 0:
                return None
            result = abs(whole) + Fraction(numerator, denominator)
            return -result if whole < 0 else result
        if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d+)?|\d+\s*/\s*\d+)", text):
            return None
        return Fraction(text.replace(" ", ""))
    except (ValueError, ZeroDivisionError):
        return None


def answers_equivalent(submitted: str, expected: str, answer_type: str | None = None) -> bool:
    """Compare answers according to the question's declared representation."""
    normalized_type = answer_type.strip().casefold() if answer_type else None
    if normalized_type in _TEXT_TYPES:
        return submitted.strip().casefold() == expected.strip().casefold()
    left, right = _fraction(submitted), _fraction(expected)
    if normalized_type in _NUMERIC_TYPES:
        return left is not None and right is not None and left == right
    if left is not None and right is not None:
        return left == right
    return submitted.strip().casefold() == expected.strip().casefold()
