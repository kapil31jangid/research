"""Command-line entry point for synthetic RAPID-Learn experiments."""

import argparse
import json
from pathlib import Path

from app.evaluation.ablations import ABLATIONS, condition_config
from app.evaluation.config import ExperimentConfig
from app.evaluation.simulator import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic RAPID-Learn experiment harness")
    parser.add_argument("command", choices=["run", "run-suite", "run-ablation-suite", "summarize"])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--seeds", nargs="*", type=int)
    parser.add_argument("--experiment", type=Path)
    args = parser.parse_args()
    config = ExperimentConfig.model_validate(json.loads(args.config.read_text(encoding="utf-8")))
    if args.command == "run":
        print(run_experiment(config))
    elif args.command == "summarize":
        directory = args.experiment
        if directory is None:
            raise SystemExit("--experiment is required for summarize")
        print((directory / "summary.json").read_text(encoding="utf-8"))
    else:
        conditions = ABLATIONS if args.command == "run-ablation-suite" else (config.condition,)
        seeds = args.seeds or [config.random_seed]
        for seed in seeds:
            for condition in conditions:
                print(
                    run_experiment(
                        condition_config(config.model_copy(update={"random_seed": seed}), condition)
                    )
                )


if __name__ == "__main__":
    main()
