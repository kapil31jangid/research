"""Command-line entry point for synthetic RAPID-Learn experiments."""

import argparse
import json
from pathlib import Path

from app.evaluation.ablations import ABLATIONS
from app.evaluation.config import ExperimentConfig
from app.evaluation.sensitivity import WEIGHT_VARIANTS, run_weight_sensitivity
from app.evaluation.simulator import run_experiment
from app.evaluation.suite import run_suite


def validate_workload(
    config: ExperimentConfig,
    condition_count: int,
    seed_count: int,
    allow_large_run: bool,
) -> None:
    workload = config.learner_count * config.interactions_per_learner * condition_count * seed_count
    if workload > config.max_interactions_without_override and not allow_large_run:
        raise SystemExit(
            f"Refusing {workload} simulated interactions; pass --allow-large-run "
            "after reviewing the experiment size."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic RAPID-Learn experiment harness")
    parser.add_argument(
        "command",
        choices=[
            "run",
            "run-suite",
            "run-ablation-suite",
            "run-sensitivity",
            "plan",
            "summarize",
        ],
    )
    parser.add_argument("--config", type=Path)
    parser.add_argument("--seeds", nargs="*", type=int)
    parser.add_argument("--experiment", type=Path)
    parser.add_argument("--allow-large-run", action="store_true")
    args = parser.parse_args()
    if args.command == "summarize":
        directory = args.experiment
        if directory is None:
            raise SystemExit("--experiment is required for summarize")
        summary = directory / "summary.json"
        if not summary.exists():
            summary = directory / "suite_summary.json"
        print(summary.read_text(encoding="utf-8"))
        return
    if args.config is None:
        raise SystemExit("--config is required for run commands")
    config = ExperimentConfig.model_validate(json.loads(args.config.read_text(encoding="utf-8")))
    seeds = args.seeds or [config.random_seed]
    if args.command == "plan":
        conditions = ABLATIONS
        workload = (
            config.learner_count * config.interactions_per_learner * len(conditions) * len(seeds)
        )
        print(
            json.dumps(
                {
                    "resolved_configuration": config.model_dump(mode="json"),
                    "config_hash": config.config_hash,
                    "conditions": list(conditions),
                    "seeds": seeds,
                    "expected_interactions": workload,
                    "output_directory": config.output_dir,
                    "isolated_database_per_condition_seed": True,
                },
                indent=2,
            )
        )
        return
    if args.command == "run":
        validate_workload(config, 1, 1, args.allow_large_run)
        print(run_experiment(config))
    elif args.command == "run-sensitivity":
        validate_workload(config, len(WEIGHT_VARIANTS), len(seeds), args.allow_large_run)
        print(run_weight_sensitivity(config, seeds))
    else:
        conditions = ABLATIONS if args.command == "run-ablation-suite" else (config.condition,)
        validate_workload(config, len(conditions), len(seeds), args.allow_large_run)
        print(run_suite(config, conditions, seeds))


if __name__ == "__main__":
    main()
