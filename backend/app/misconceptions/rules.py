"""Load and validate misconception rules kept outside application code."""

from pathlib import Path

from pydantic import BaseModel, Field


class MisconceptionRule(BaseModel):
    id: str
    concept_ids: list[str] = Field(min_length=1)
    minimum_evidence: int = Field(ge=2)
    recent_window: int = Field(ge=2)
    pattern_labels: list[str] = Field(min_length=1)
    explanation: str
    remediation_activity: str


def load_rules() -> list[MisconceptionRule]:
    """Read fraction rules from the versioned JSON data file."""
    data_path = Path(__file__).resolve().parents[3] / "data/misconceptions/fractions.json"
    return [MisconceptionRule.model_validate_json(line) for line in _items(data_path)]


def _items(data_path: Path) -> list[str]:
    """Convert JSON objects to Pydantic-compatible JSON strings."""
    import json

    with data_path.open(encoding="utf-8") as source:
        content = json.load(source)
    if not isinstance(content, list):
        raise ValueError("Misconception rules must be a JSON list")
    return [json.dumps(item) for item in content]
