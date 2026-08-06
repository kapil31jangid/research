"""Load versioned curriculum seed files."""

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = PROJECT_ROOT / "data"


def load_json(relative_path: str) -> list[dict[str, Any]]:
    """Read a JSON list from the repository data directory."""
    with (DATA_ROOT / relative_path).open(encoding="utf-8") as source:
        content = json.load(source)
    if not isinstance(content, list):
        raise ValueError(f"Expected a list in {relative_path}")
    return content


def load_concepts() -> list[dict[str, Any]]:
    return load_json("curriculum/fractions.json")


def load_questions() -> list[dict[str, Any]]:
    return load_json("questions/fractions.json")
