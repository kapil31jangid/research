"""Rule-based detector requiring repeated recent matching evidence."""

from dataclasses import dataclass
from datetime import datetime

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
    interactions: list[InteractionEvidence], rules: list[MisconceptionRule]
) -> list[MisconceptionDetection]:
    """Detect only rules supported by at least two matching recent errors."""
    detections: list[MisconceptionDetection] = []
    for rule in rules:
        relevant = [
            interaction
            for interaction in sorted(interactions, key=lambda item: item.timestamp, reverse=True)[
                : rule.recent_window
            ]
            if interaction.concept_id in rule.concept_ids
            and not interaction.correct
            and set(interaction.pattern_labels).intersection(rule.pattern_labels)
        ]
        count = len(relevant)
        if count >= rule.minimum_evidence:
            confidence = min(1.0, 0.55 + 0.15 * (count - rule.minimum_evidence + 1))
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
