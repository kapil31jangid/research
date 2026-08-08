"""Multi-condition, multi-seed execution and aggregate research artifacts."""

import json
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from app.evaluation.ablations import condition_config
from app.evaluation.config import ExperimentConfig
from app.evaluation.ml_metrics import matched_prediction_outcomes
from app.evaluation.plots import write_suite_plots
from app.evaluation.simulator import run_experiment
from app.evaluation.statistics import (
    bootstrap_confidence_interval,
    cohens_d,
    paired_bootstrap_difference,
)
from app.evaluation.tables import write_suite_tables

PAIRED_CONDITIONS = (
    "no_ml",
    "no_misconceptions",
    "no_resource_awareness",
    "no_forgetting",
    "no_uncertainty",
    "no_offline_adaptation",
    "bkt_only",
    "static_baseline",
)
PAIRED_METRICS = (
    "mean_final_mastery",
    "mean_mastery_gain",
    "mean_synthetic_mastery_gain",
    "mastery_threshold_success_rate",
    "misconception_resolution_rate",
    "mean_latency",
    "p95_latency",
    "mean_estimated_compute_cost_ms",
)


def _execute_run(job: tuple[dict[str, object], str, int]) -> str:
    """Execute one isolated condition/seed run in a worker process."""
    config_data, condition, seed = job
    base = ExperimentConfig.model_validate(config_data | {"random_seed": seed})
    return str(run_experiment(condition_config(base, condition)))


def paired_comparisons(
    seed_metrics: pd.DataFrame,
    config: ExperimentConfig,
) -> pd.DataFrame:
    """Build reproducible full-versus-ablation comparisons from seed summaries."""
    rows: list[dict[str, object]] = []
    full = seed_metrics.loc[seed_metrics.condition == "full"]
    for condition in PAIRED_CONDITIONS:
        other = seed_metrics.loc[seed_metrics.condition == condition]
        paired = full.merge(other, on="random_seed", suffixes=("_reference", "_comparison"))
        for metric in PAIRED_METRICS:
            left = f"{metric}_reference"
            right = f"{metric}_comparison"
            if left not in paired or right not in paired:
                continue
            valid = paired[[left, right]].dropna()
            if valid.empty:
                continue
            reference = valid[left].astype(float).tolist()
            comparison = valid[right].astype(float).tolist()
            difference, low, high = paired_bootstrap_difference(
                reference,
                comparison,
                config.random_seed,
                samples=config.bootstrap_samples,
            )
            rows.append(
                {
                    "metric": metric,
                    "reference_condition": "full",
                    "comparison_condition": condition,
                    "mean_difference": difference,
                    "ci_low": low,
                    "ci_high": high,
                    "effect_size": cohens_d(reference, comparison),
                    "matched_seed_count": len(valid),
                }
            )
    return pd.DataFrame(rows)


def run_suite(
    config: ExperimentConfig,
    conditions: tuple[str, ...],
    seeds: list[int],
) -> Path:
    suite_id = f"{datetime.now(UTC):%Y-%m-%d_%H%M%S}_{config.experiment_name}"
    directory = Path(config.output_dir) / "suites" / suite_id
    directory.mkdir(parents=True)
    records: list[dict[str, object]] = []
    interaction_frames: list[pd.DataFrame] = []
    matched_frames: list[pd.DataFrame] = []
    jobs = [(config.model_dump(), condition, seed) for seed in seeds for condition in conditions]
    if config.suite_workers == 1:
        run_directories = [_execute_run(job) for job in jobs]
    else:
        with ProcessPoolExecutor(max_workers=config.suite_workers) as executor:
            run_directories = list(executor.map(_execute_run, jobs))
    for run_directory_text in run_directories:
        run_directory = Path(run_directory_text)
        records.append(
            json.loads((run_directory / "summary.json").read_text(encoding="utf-8"))
            | {"run_directory": str(run_directory)}
        )
        interaction_frame = pd.read_parquet(run_directory / "interactions.parquet")
        interaction_frame["run_directory"] = str(run_directory)
        interaction_frames.append(interaction_frame)
        matched = matched_prediction_outcomes(interaction_frame)
        if not matched.empty:
            matched["condition"] = interaction_frame["condition"].iloc[0]
            matched_frames.append(matched)
    seed_metrics = pd.DataFrame(records)
    seed_metrics.to_csv(directory / "seed_metrics.csv", index=False)
    numeric = [
        column
        for column in seed_metrics.select_dtypes(include="number").columns
        if column not in {"random_seed"}
    ]
    aggregate_rows: list[dict[str, object]] = []
    for condition, group in seed_metrics.groupby("condition"):
        for metric in numeric:
            values = group[metric].dropna().astype(float).tolist()
            if not values:
                continue
            low, high = bootstrap_confidence_interval(
                values, config.random_seed, samples=config.bootstrap_samples
            )
            aggregate_rows.append(
                {
                    "condition": condition,
                    "metric": metric,
                    "mean": sum(values) / len(values),
                    "between_seed_variance": pd.Series(values).var(ddof=1)
                    if len(values) > 1
                    else 0.0,
                    "ci_low": low,
                    "ci_high": high,
                    "seed_count": len(values),
                }
            )
    aggregate = pd.DataFrame(aggregate_rows)
    aggregate.to_csv(directory / "aggregate_metrics.csv", index=False)
    paired_frame = paired_comparisons(seed_metrics, config)
    paired_frame.to_csv(directory / "paired_comparisons.csv", index=False)
    summary = {
        "simulated_results": True,
        "data_source": "synthetic",
        "educational_effectiveness_validated": False,
        "suite_id": suite_id,
        "config_hash": config.config_hash,
        "conditions": list(conditions),
        "seeds": seeds,
        "run_count": len(records),
        "bootstrap_samples": config.bootstrap_samples,
        "suite_workers": config.suite_workers,
    }
    (directory / "suite_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    combined_interactions = pd.concat(interaction_frames, ignore_index=True)
    combined_interactions.to_parquet(directory / "interactions.parquet", index=False)
    combined_matched = (
        pd.concat(matched_frames, ignore_index=True)
        if matched_frames
        else pd.DataFrame(columns=["probability", "outcome", "condition"])
    )
    write_suite_plots(
        seed_metrics, paired_frame, combined_interactions, combined_matched, directory
    )
    write_suite_tables(seed_metrics, paired_frame, combined_interactions, directory)
    return directory
