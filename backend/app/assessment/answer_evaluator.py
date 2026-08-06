"""Deterministic mathematical answer equivalence without expression evaluation."""

import re
from fractions import Fraction

_MIXED = re.compile(r"^([+-]?\d+)\s+(\d+)\s*/\s*(\d+)$")


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
    left, right = _fraction(submitted), _fraction(expected)
    if left is not None and right is not None:
        return left == right
    return submitted.strip().casefold() == expected.strip().casefold()
