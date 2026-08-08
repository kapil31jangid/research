"""Command-line entry point for synthetic RAPID-Learn experiments."""

import argparse
import json
from pathlib import Path

from app.evaluation.config import ExperimentConfig
from app.evaluation.simulator import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic RAPID-Learn experiment harness")
    parser.add_argument("run", choices=["run"])
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = ExperimentConfig.model_validate(json.loads(args.config.read_text(encoding="utf-8")))
    print(run_experiment(config))


if __name__ == "__main__":
    main()
