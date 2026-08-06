"""Prerequisite-mastery calculations and eligibility decisions."""

from dataclasses import dataclass

import networkx as nx

from app.curriculum.graph import prerequisite_ids


@dataclass(frozen=True)
class PrerequisiteStatus:
    concept_id: str
    mastery: float
    blocked_prerequisites: list[str]

    @property
    def eligible(self) -> bool:
        return not self.blocked_prerequisites


def prerequisite_mastery(
    graph: nx.DiGraph, concept_id: str, mastery_by_concept: dict[str, float]
) -> float:
    """Calculate mean direct-prerequisite mastery, or 1.0 when none are needed."""
    required = prerequisite_ids(graph, concept_id)
    if not required:
        return 1.0
    return sum(mastery_by_concept.get(item, 0.0) for item in required) / len(required)


def prerequisite_status(
    graph: nx.DiGraph,
    concept_id: str,
    mastery_by_concept: dict[str, float],
    threshold_by_concept: dict[str, float],
) -> PrerequisiteStatus:
    """Report whether all direct prerequisites have reached their own threshold."""
    required = prerequisite_ids(graph, concept_id)
    blocked = [
        item
        for item in required
        if mastery_by_concept.get(item, 0.0) < threshold_by_concept.get(item, 0.75)
    ]
    return PrerequisiteStatus(
        concept_id=concept_id,
        mastery=prerequisite_mastery(graph, concept_id, mastery_by_concept),
        blocked_prerequisites=blocked,
    )


def next_eligible_concepts(
    graph: nx.DiGraph,
    mastery_by_concept: dict[str, float],
    threshold_by_concept: dict[str, float],
) -> list[str]:
    """Return unmet concepts whose prerequisite gates are open."""
    return [
        concept_id
        for concept_id in graph.nodes
        if mastery_by_concept.get(concept_id, 0.0) < threshold_by_concept.get(concept_id, 0.75)
        and prerequisite_status(
            graph, concept_id, mastery_by_concept, threshold_by_concept
        ).eligible
    ]
