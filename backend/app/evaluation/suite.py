"""Multi-condition, multi-seed execution and aggregate research artifacts."""

import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from app.evaluation.ablations import condition_config, condition_matrix
from app.evaluation.config import ExperimentConfig
from app.evaluation.ml_metrics import matched_prediction_outcomes
from app.evaluation.plots import write_suite_plots
from app.evaluation.provenance import collect_provenance
from app.evaluation.publication import publish_suite
from app.evaluation.simulator import run_experiment
from app.evaluation.statistics import (
    bootstrap_confidence_interval,
    cohens_d,
    paired_bootstrap_difference,
)
from app.evaluation.synthetic_learners import PROFILES
from app.evaluation.tables import write_suite_tables
from app.ml_runtime.model_registry import get_response_predictor_registry

PAIRED_CONDITIONS = (
    "static_baseline",
    "bkt_only",
    "bkt_uncertainty",
    "pedagogical_adaptive",
    "no_uncertainty",
    "no_forgetting",
    "no_misconceptions",
    "no_resource_awareness",
    "no_offline_adaptation",
    "no_ml",
)
PAIRED_METRICS = (
    "response_accuracy",
    "mean_final_mastery",
    "mean_mastery_gain",
    "mean_normalised_gain",
    "mean_retention",
    "mean_synthetic_mastery_gain",
    "mean_synthetic_normalised_gain",
    "mastery_threshold_success_rate",
    "misconception_resolution_rate",
    "prerequisite_violation_rate",
    "mean_latency",
    "p95_latency",
    "mean_estimated_compute_cost_ms",
    "resource_normalised_utility",
    "offline_recommendation_availability",
)


def _execute_run(job: tuple[dict[str, object], str, int]) -> tuple[str, bool]:
    """Execute one isolated condition/seed run in a worker process."""
    config_data, condition, seed = job
    base = ExperimentConfig.model_validate(config_data | {"random_seed": seed})
    resolved = condition_config(base, condition)
    if resolved.reuse_completed_runs:
        pattern = f"*_{condition}_seed{seed}*"
        for candidate in sorted(Path(resolved.output_dir).glob(pattern), reverse=True):
            try:
                stored = ExperimentConfig.model_validate_json(
                    (candidate / "config.json").read_text(encoding="utf-8")
                )
                summary = json.loads((candidate / "summary.json").read_text(encoding="utf-8"))
            except (OSError, ValueError, KeyError):
                continue
            expected = resolved.learner_count * resolved.interactions_per_learner
            if (
                stored.config_hash == resolved.config_hash
                and summary.get("interaction_count") == expected
                and summary.get("integrity", {}).get("valid") is True
            ):
                return str(candidate), True
    return str(run_experiment(resolved)), False


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
    learner_frames: list[pd.DataFrame] = []
    concept_frames: list[pd.DataFrame] = []
    matched_frames: list[pd.DataFrame] = []
    jobs = [(config.model_dump(), condition, seed) for seed in seeds for condition in conditions]
    if config.suite_workers == 1:
        completed_runs = []
        for index, job in enumerate(jobs, start=1):
            completed_runs.append(_execute_run(job))
            print(f"completed experiment run {index}/{len(jobs)}", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=config.suite_workers) as executor:
            completed_runs = []
            for index, completed in enumerate(executor.map(_execute_run, jobs), start=1):
                completed_runs.append(completed)
                print(f"completed experiment run {index}/{len(jobs)}", flush=True)
    run_directories = [path for path, _reused in completed_runs]
    reused_run_count = sum(reused for _path, reused in completed_runs)
    for run_directory_text in run_directories:
        run_directory = Path(run_directory_text)
        records.append(
            json.loads((run_directory / "summary.json").read_text(encoding="utf-8"))
            | {"run_directory": str(run_directory)}
        )
        interaction_frame = pd.read_parquet(run_directory / "interactions.parquet")
        interaction_frame["run_directory"] = str(run_directory)
        interaction_frames.append(interaction_frame)
        learner_frame = pd.read_parquet(run_directory / "learners.parquet")
        learner_frame["condition"] = interaction_frame["condition"].iloc[0]
        learner_frame["seed"] = int(interaction_frame["seed"].iloc[0])
        learner_frame["run_directory"] = str(run_directory)
        learner_frames.append(learner_frame)
        concept_frame = pd.read_parquet(run_directory / "concept_outcomes.parquet")
        concept_frame["run_directory"] = str(run_directory)
        concept_frames.append(concept_frame)
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
                    "std": pd.Series(values).std(ddof=1) if len(values) > 1 else 0.0,
                    "ci_low": low,
                    "ci_high": high,
                    "seed_count": len(values),
                }
            )
    aggregate = pd.DataFrame(aggregate_rows)
    aggregate.to_csv(directory / "aggregate_metrics.csv", index=False)
    aggregate.to_csv(directory / "confidence_intervals.csv", index=False)
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
        "harness_version": config.harness_version,
        "reused_run_count": reused_run_count,
    }
    (directory / "suite_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (directory / "config.json").write_text(config.model_dump_json(indent=2), encoding="utf-8")
    configuration_directory = directory / "config"
    configuration_directory.mkdir(exist_ok=True)
    pd.DataFrame(condition_matrix(config)).to_csv(
        configuration_directory / "condition_matrix.csv", index=False
    )
    (configuration_directory / "condition_matrix.json").write_text(
        json.dumps(condition_matrix(config), indent=2), encoding="utf-8"
    )
    publication_profile_names = set(config.learner_profile_distribution)
    (configuration_directory / "synthetic_profiles.json").write_text(
        json.dumps(
            {
                name: asdict(PROFILES[name])
                | {"assumption_status": "heuristic_synthetic_parameter"}
                for name in sorted(publication_profile_names)
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (directory / "provenance.json").write_text(
        json.dumps(
            collect_provenance(get_response_predictor_registry().get_model_version())
            | {
                "config_hash": config.config_hash,
                "conditions": list(conditions),
                "seeds": seeds,
                "simulated_results": True,
                "data_source": "synthetic",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    combined_interactions = pd.concat(interaction_frames, ignore_index=True)
    expected_interactions = (
        config.learner_count * config.interactions_per_learner * len(conditions) * len(seeds)
    )
    duplicate_count = int(
        combined_interactions.duplicated(
            ["condition", "seed", "synthetic_learner_id", "step"]
        ).sum()
    )
    if len(combined_interactions) != expected_interactions or duplicate_count:
        raise ValueError(
            "Suite interaction integrity failed: "
            f"expected={expected_interactions}, actual={len(combined_interactions)}, "
            f"duplicates={duplicate_count}"
        )
    summary["expected_interaction_count"] = expected_interactions
    summary["actual_interaction_count"] = len(combined_interactions)
    summary["duplicate_interaction_count"] = duplicate_count
    summary["integrity_valid"] = True
    (directory / "suite_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    combined_interactions.to_parquet(directory / "interactions.parquet", index=False)
    if config.publish_paper_layout:
        combined_interactions.to_csv(directory / "interactions.csv", index=False)
    combined_learners = pd.concat(learner_frames, ignore_index=True)
    combined_learners.to_parquet(directory / "learner_metrics.parquet", index=False)
    combined_learners.to_csv(directory / "learner_metrics.csv", index=False)
    combined_concepts = pd.concat(concept_frames, ignore_index=True)
    combined_concepts.to_parquet(directory / "concept_metrics.parquet", index=False)
    combined_concepts.to_csv(directory / "concept_metrics.csv", index=False)
    resource_columns = [
        "condition",
        "random_seed",
        "mean_resource_score",
        "mean_memory_pressure",
        "mean_memory_used_mb",
        "mean_cpu_percent",
        "mean_bandwidth_kb",
        "mean_latency",
        "p95_latency",
        "mean_estimated_compute_cost_ms",
        "resource_normalised_utility",
    ]
    seed_metrics[[column for column in resource_columns if column in seed_metrics]].to_csv(
        directory / "resource_metrics.csv", index=False
    )
    offline_columns = [
        "condition",
        "random_seed",
        "offline_adaptation_rate",
        "offline_recommendation_availability",
        "offline_content_miss_rate",
        "matching_offline_activity_count",
    ]
    seed_metrics[[column for column in offline_columns if column in seed_metrics]].to_csv(
        directory / "offline_metrics.csv", index=False
    )
    ml_columns = [
        column
        for column in seed_metrics.columns
        if column in {"condition", "random_seed", "ml_usage_rate", "fallback_rate"}
        or column.startswith("synthetic_ml_")
        or column.startswith("synthetic_brier")
        or column.startswith("synthetic_log")
        or column.startswith("synthetic_roc")
        or column.startswith("synthetic_accuracy")
        or column.startswith("synthetic_expected_calibration")
    ]
    seed_metrics[ml_columns].to_csv(directory / "ml_metrics.csv", index=False)
    combined_matched = (
        pd.concat(matched_frames, ignore_index=True)
        if matched_frames
        else pd.DataFrame(columns=["probability", "outcome", "condition"])
    )
    write_suite_plots(
        seed_metrics,
        paired_frame,
        combined_interactions,
        combined_matched,
        directory,
        config.random_seed,
        config.bootstrap_samples,
    )
    write_suite_tables(seed_metrics, paired_frame, combined_interactions, directory)
    if config.publish_paper_layout:
        publish_suite(directory, Path(config.output_dir).parent)
    return directory
