"""Portable CSV, Markdown, and LaTeX summaries for synthetic conditions."""

from pathlib import Path

import pandas as pd


def write_condition_table(interactions: pd.DataFrame, directory: Path) -> pd.DataFrame:
    grouped = interactions.groupby("condition", as_index=False).agg(
        Final_Mastery=("system_mastery_after", "mean"),
        Mean_Latency_ms=("measured_total_adaptive_latency_ms", "mean"),
        Fallback_Rate=("fallback_used", "mean"),
    )
    grouped.to_csv(directory / "condition_metrics.csv", index=False)
    (directory / "tables").mkdir(exist_ok=True)
    columns = list(grouped.columns)
    markdown = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    markdown.extend(
        "| " + " | ".join(map(str, row)) + " |"
        for row in grouped.itertuples(index=False, name=None)
    )
    (directory / "tables" / "main_comparison.md").write_text("\n".join(markdown), encoding="utf-8")
    latex = [
        "\\begin{tabular}{" + "l" * len(columns) + "}",
        " & ".join(columns) + "\\\\",
        "\\hline",
    ]
    latex.extend(
        " & ".join(map(str, row)) + "\\\\" for row in grouped.itertuples(index=False, name=None)
    )
    latex.append("\\end{tabular}")
    (directory / "tables" / "main_comparison.tex").write_text("\n".join(latex), encoding="utf-8")
    return grouped


def _write_formats(frame: pd.DataFrame, stem: Path) -> None:
    frame.to_csv(stem.with_suffix(".csv"), index=False)
    columns = list(frame.columns)
    rows = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    rows.extend(
        "| " + " | ".join(map(str, row)) + " |" for row in frame.itertuples(index=False, name=None)
    )
    stem.with_suffix(".md").write_text("\n".join(rows), encoding="utf-8")
    escaped = [column.replace("_", "\\_") for column in columns]
    latex = [
        "\\begin{tabular}{" + "l" * len(columns) + "}",
        " & ".join(escaped) + "\\\\",
        "\\hline",
    ]
    latex.extend(
        " & ".join(str(value).replace("_", "\\_") for value in row) + "\\\\"
        for row in frame.itertuples(index=False, name=None)
    )
    latex.append("\\end{tabular}")
    stem.with_suffix(".tex").write_text("\n".join(latex), encoding="utf-8")


def write_suite_tables(
    seed_metrics: pd.DataFrame,
    paired: pd.DataFrame,
    interactions: pd.DataFrame,
    directory: Path,
) -> None:
    tables = directory / "tables"
    tables.mkdir(exist_ok=True)
    fields = {
        "mean_initial_mastery": "Initial System Mastery",
        "mean_final_mastery": "Final System Mastery",
        "mean_mastery_gain": "System Mastery Gain",
        "mean_synthetic_mastery_gain": "Synthetic Mastery Gain",
        "mastery_threshold_success_rate": "Threshold Success",
        "median_interactions_to_threshold": "Interactions to Threshold",
        "misconception_resolution_rate": "Misconception Resolution",
        "mean_latency": "Mean Latency",
        "p95_latency": "p95 Latency",
        "mean_estimated_compute_cost_ms": "Estimated Compute Cost",
    }
    available = [field for field in fields if field in seed_metrics]
    main = (
        seed_metrics.groupby("condition", as_index=False)[available]
        .mean()
        .rename(columns={"condition": "Condition"} | {field: fields[field] for field in available})
    )
    _write_formats(main, tables / "main_comparison")
    _write_formats(paired, tables / "ablation_comparisons")
    ml_fields = [
        "condition",
        "synthetic_ml_matched_samples",
        "synthetic_brier_score",
        "synthetic_log_loss",
        "synthetic_roc_auc",
        "synthetic_expected_calibration_error",
        "ml_usage_rate",
        "fallback_rate",
    ]
    available_ml = [field for field in ml_fields if field in seed_metrics]
    ml = seed_metrics.groupby("condition", as_index=False)[
        [field for field in available_ml if field != "condition"]
    ].mean()
    _write_formats(ml, tables / "ml_metrics")
    path_rates = pd.crosstab(
        interactions.resource_profile,
        interactions.actual_adaptation_path,
        normalize="index",
    ).reset_index()
    resources = (
        interactions.groupby("resource_profile", as_index=False)
        .agg(
            mean_resource_score=("resource_score", "mean"),
            mean_latency=("measured_total_adaptive_latency_ms", "mean"),
        )
        .merge(path_rates, on="resource_profile", how="left")
    )
    _write_formats(resources, tables / "resource_profiles")
