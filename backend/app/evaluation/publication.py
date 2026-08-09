"""Arrange validated suite artifacts into the paper-facing directory layout."""

import json
import os
import shutil
from pathlib import Path

import pandas as pd


def _link_or_copy(source: Path, destination: Path) -> None:
    destination.unlink(missing_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def publish_suite(suite_directory: Path, paper_root: Path) -> Path:
    """Publish one fully validated suite without duplicating large Parquet files."""
    summary = json.loads((suite_directory / "suite_summary.json").read_text(encoding="utf-8"))
    if not summary.get("integrity_valid"):
        raise ValueError("Cannot publish a suite that has not passed integrity validation")
    for name in ("raw", "aggregate", "tables", "plots", "metadata", "config"):
        (paper_root / name).mkdir(parents=True, exist_ok=True)
    for filename in (
        "interactions.parquet",
        "interactions.csv",
        "learner_metrics.parquet",
        "learner_metrics.csv",
        "concept_metrics.parquet",
        "concept_metrics.csv",
    ):
        _link_or_copy(suite_directory / filename, paper_root / "raw" / filename)
    aggregate_files = (
        "seed_metrics.csv",
        "aggregate_metrics.csv",
        "confidence_intervals.csv",
        "paired_comparisons.csv",
        "resource_metrics.csv",
        "offline_metrics.csv",
        "ml_metrics.csv",
    )
    for filename in aggregate_files:
        shutil.copy2(suite_directory / filename, paper_root / "aggregate" / filename)
    shutil.copy2(
        suite_directory / "paired_comparisons.csv",
        paper_root / "aggregate" / "ablation_comparisons.csv",
    )
    for directory_name in ("tables", "plots", "config"):
        shutil.copytree(
            suite_directory / directory_name,
            paper_root / directory_name,
            dirs_exist_ok=True,
        )
    for filename in ("suite_summary.json", "provenance.json"):
        shutil.copy2(suite_directory / filename, paper_root / "metadata" / filename)
    shutil.copy2(suite_directory / "config.json", paper_root / "config" / "final_study.json")
    seed_metrics = pd.read_csv(suite_directory / "seed_metrics.csv")
    for seed, rows in seed_metrics.groupby("random_seed"):
        seed_directory = paper_root / f"seed_{int(seed)}"
        seed_directory.mkdir(exist_ok=True)
        rows.to_csv(seed_directory / "condition_metrics.csv", index=False)
        (seed_directory / "run_manifest.json").write_text(
            json.dumps(
                {
                    "seed": int(seed),
                    "conditions": rows.condition.tolist(),
                    "run_directories": rows.run_directory.tolist(),
                    "simulated_results": True,
                    "data_source": "synthetic",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return paper_root
