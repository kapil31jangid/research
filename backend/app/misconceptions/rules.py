"""Load and validate misconception rules kept outside application code."""

from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class MisconceptionRule(BaseModel):
    id: str
    concept_ids: list[str] = Field(min_length=1)
    # Rules may tune these values, otherwise the experiment configuration supplies
    # one consistent default across the curriculum.
    minimum_evidence: int | None = Field(default=None, ge=2)
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    recent_window: int | None = Field(default=None, ge=2)
    pattern_labels: list[str] = Field(min_length=1)
    explanation: str
    remediation_activity: str

    @model_validator(mode="after")
    def validate_evidence_override(self) -> "MisconceptionRule":
        if (
            self.minimum_evidence is not None
            and self.recent_window is not None
            and self.minimum_evidence > self.recent_window
        ):
            raise ValueError("Rule minimum evidence cannot exceed its recent window")
        return self


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
