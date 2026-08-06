"""Typed feature contract shared by model training and runtime inference."""

from pydantic import BaseModel


class ResponsePredictionFeatures(BaseModel):
    mastery: float
    retained_mastery: float
    uncertainty: float
    question_difficulty: float
    concept_difficulty: float
    recent_correctness: float
    average_response_time: float
    response_time_variation: float
    hint_usage_rate: float
    attempts: float
    correct_attempts: float
    prerequisite_mastery: float
    days_since_practice: float
    misconception_confidence: float
    resource_score: float
