"""Rule-based detector requiring repeated recent matching evidence."""

from dataclasses import dataclass
from datetime import datetime

from app.core.config import Settings, get_settings
from app.misconceptions.rules import MisconceptionRule


@dataclass(frozen=True)
class InteractionEvidence:
    concept_id: str
    correct: bool
    pattern_labels: list[str]
    timestamp: datetime


@dataclass(frozen=True)
class MisconceptionDetection:
    id: str
    confidence: float
    evidence_count: int
    explanation: str
    remediation_activity: str


def detect_misconceptions(
    interactions: list[InteractionEvidence],
    rules: list[MisconceptionRule],
    settings: Settings | None = None,
) -> list[MisconceptionDetection]:
    """Return rule detections supported by recent, concept-relevant error evidence."""
    settings = settings or get_settings()
    detections: list[MisconceptionDetection] = []
    for rule in rules:
        recent_window = rule.recent_window or settings.misconception_evidence_window
        minimum_evidence = rule.minimum_evidence or settings.misconception_minimum_evidence
        confidence_threshold = rule.confidence_threshold or settings.misconception_default_threshold
        relevant = [
            interaction
            for interaction in sorted(interactions, key=lambda item: item.timestamp, reverse=True)
            if interaction.concept_id in rule.concept_ids
            and not interaction.correct
            and set(interaction.pattern_labels).intersection(rule.pattern_labels)
        ][:recent_window]
        count = len(relevant)
        if count >= minimum_evidence:
            confidence = min(1.0, 0.55 + 0.15 * (count - minimum_evidence + 1))
            if confidence < confidence_threshold:
                continue
            detections.append(
                MisconceptionDetection(
                    id=rule.id,
                    confidence=confidence,
                    evidence_count=count,
                    explanation=rule.explanation,
                    remediation_activity=rule.remediation_activity,
                )
            )
    return sorted(detections, key=lambda item: item.confidence, reverse=True)
