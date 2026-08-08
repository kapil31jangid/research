import pytest

from app.curriculum.graph import build_graph
from app.curriculum.loader import load_concepts, load_questions


def test_seed_data_meets_foundation_minimums():
    assert len(load_concepts()) >= 12
    assert len(load_questions()) >= 100
    assert build_graph(load_concepts()).number_of_nodes() == 16


def test_graph_rejects_cycle():
    concepts = [
        {"id": "a", "name": "A", "prerequisite_ids": ["b"]},
        {"id": "b", "name": "B", "prerequisite_ids": ["a"]},
    ]
    with pytest.raises(ValueError, match="cycle"):
        build_graph(concepts)
