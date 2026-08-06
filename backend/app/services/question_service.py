"""Question read-model conversion shared by selection and HTTP routes."""

import json

from app.models.question import Question


def serialise_question(question: Question) -> dict[str, object]:
    """Return learner-safe question data without its correct answer."""
    return {
        "id": question.id,
        "concept_id": question.concept_id,
        "text": question.text,
        "answer_type": question.answer_type,
        "options": json.loads(question.options),
        "difficulty": question.difficulty,
        "explanation": question.explanation,
        "diagnostic_value": question.diagnostic_value,
        "estimated_cost_ms": question.estimated_cost_ms,
        "misconception_patterns": json.loads(question.misconception_patterns),
        "template_id": question.template_id,
    }
