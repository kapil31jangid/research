"""NetworkX representation of the prerequisite curriculum."""

import networkx as nx


def build_graph(concepts: list[dict[str, object]]) -> nx.DiGraph:
    """Build and validate a directed graph with prerequisite -> concept edges."""
    graph = nx.DiGraph()
    ids = {str(concept["id"]) for concept in concepts}
    for concept in concepts:
        concept_id = str(concept["id"])
        graph.add_node(concept_id, name=concept["name"])
        for prerequisite_id in concept.get("prerequisite_ids", []):
            prerequisite = str(prerequisite_id)
            if prerequisite not in ids:
                raise ValueError(f"Unknown prerequisite {prerequisite} for {concept_id}")
            graph.add_edge(prerequisite, concept_id)
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Curriculum prerequisite graph contains a cycle")
    return graph


def graph_as_json(concepts: list[dict[str, object]]) -> dict[str, object]:
    graph = build_graph(concepts)
    return {
        "nodes": [{"id": node, **graph.nodes[node]} for node in graph.nodes],
        "edges": [{"source": source, "target": target} for source, target in graph.edges],
    }


def prerequisite_ids(graph: nx.DiGraph, concept_id: str, transitive: bool = False) -> list[str]:
    """Return direct or transitive prerequisite identifiers in stable order."""
    if concept_id not in graph:
        raise KeyError(f"Unknown concept: {concept_id}")
    values = nx.ancestors(graph, concept_id) if transitive else graph.predecessors(concept_id)
    return sorted(values)


def descendants(graph: nx.DiGraph, concept_id: str) -> list[str]:
    """Return all concepts unlocked downstream by a concept."""
    if concept_id not in graph:
        raise KeyError(f"Unknown concept: {concept_id}")
    return sorted(nx.descendants(graph, concept_id))
