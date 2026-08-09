"""Controlled resource- and activity-weight sensitivity experiments."""

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

from app.evaluation.config import ExperimentConfig
from app.evaluation.simulator import run_experiment
from app.evaluation.tables import _write_formats

WEIGHT_VARIANTS: dict[str, dict[str, float]] = {
    "default": {},
    "resource_A": {
        "resource_memory_weight": 0.30,
        "resource_cpu_weight": 0.30,
        "resource_battery_weight": 0.20,
        "resource_network_weight": 0.20,
    },
    "resource_B": {
        "resource_memory_weight": 0.40,
        "resource_cpu_weight": 0.20,
        "resource_battery_weight": 0.20,
        "resource_network_weight": 0.20,
    },
    "resource_C": {
        "resource_memory_weight": 0.35,
        "resource_cpu_weight": 0.25,
        "resource_battery_weight": 0.25,
        "resource_network_weight": 0.15,
    },
    "activity_A": {
        "activity_gain_weight": 0.25,
        "activity_prerequisite_weight": 0.25,
    },
    "activity_B": {
        "activity_gain_weight": 0.35,
        "activity_prerequisite_weight": 0.15,
    },
    "activity_C": {
        "activity_retention_weight": 0.25,
        "activity_information_weight": 0.10,
    },
}


def _run_variant(job: tuple[dict[str, object], str, int]) -> tuple[str, int, str]:
    config_data, variant, seed = job
    config = ExperimentConfig.model_validate(
        config_data
        | WEIGHT_VARIANTS[variant]
        | {
            "condition": "full",
            "random_seed": seed,
            "experiment_name": f"weight-{variant}",
            "publish_paper_layout": False,
        }
    )
    return variant, seed, str(run_experiment(config))


def run_weight_sensitivity(config: ExperimentConfig, seeds: list[int]) -> Path:
    """Run the same full condition under small, predeclared weight perturbations."""
    jobs = [(config.model_dump(), variant, seed) for seed in seeds for variant in WEIGHT_VARIANTS]
    if config.suite_workers == 1:
        completed = [_run_variant(job) for job in jobs]
    else:
        with ProcessPoolExecutor(max_workers=config.suite_workers) as executor:
            completed = list(executor.map(_run_variant, jobs))
    frames: dict[tuple[str, int], pd.DataFrame] = {}
    summaries: dict[tuple[str, int], dict[str, object]] = {}
    for variant, seed, directory_text in completed:
        directory = Path(directory_text)
        frames[(variant, seed)] = pd.read_parquet(directory / "interactions.parquet")
        summaries[(variant, seed)] = json.loads(
            (directory / "summary.json").read_text(encoding="utf-8")
        )
    rows: list[dict[str, object]] = []
    identity = ["synthetic_learner_id", "step"]
    for variant in WEIGHT_VARIANTS:
        for seed in seeds:
            frame = frames[(variant, seed)]
            baseline = frames[("default", seed)][identity + ["selected_activity_id"]]
            comparison = frame[identity + ["selected_activity_id"]]
            aligned = baseline.merge(comparison, on=identity, suffixes=("_default", "_variant"))
            summary = summaries[(variant, seed)]
            rows.append(
                {
                    "variant": variant,
                    "seed": seed,
                    "recommendation_stability": float(
                        (
                            aligned.selected_activity_id_default
                            == aligned.selected_activity_id_variant
                        ).mean()
                    ),
                    "normalized_gain": summary["mean_synthetic_normalised_gain"],
                    "retention": summary["mean_synthetic_retention"],
                    "mean_latency_ms": summary["mean_latency"],
                    "resource_normalised_utility": summary["resource_normalised_utility"],
                    "config_hash": summary["config_hash"],
                    "interaction_count": summary["interaction_count"],
                }
            )
    result = pd.DataFrame(rows)
    paper_root = Path(config.output_dir).parent
    aggregate = paper_root / "aggregate"
    tables = paper_root / "tables"
    aggregate.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    output = aggregate / "weight_sensitivity.csv"
    result.to_csv(output, index=False)
    table = result.groupby("variant", as_index=False).agg(
        Recommendation_Stability=("recommendation_stability", "mean"),
        Normalized_Gain=("normalized_gain", "mean"),
        Retention=("retention", "mean"),
        Mean_Latency_ms=("mean_latency_ms", "mean"),
        Resource_Normalized_Utility=("resource_normalised_utility", "mean"),
    )
    _write_formats(table, tables / "weight_sensitivity")
    return output
