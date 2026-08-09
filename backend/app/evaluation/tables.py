"""Portable CSV, Markdown, and LaTeX summaries for synthetic conditions."""

from dataclasses import asdict
from pathlib import Path

import pandas as pd

from app.evaluation.statistics import bootstrap_confidence_interval
from app.evaluation.synthetic_learners import PROFILES


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
    bootstrap_seed: int = 42,
    bootstrap_samples: int = 10_000,
) -> None:
    tables = directory / "tables"
    tables.mkdir(exist_ok=True)
    fields = {
        "response_accuracy": "Accuracy",
        "mean_synthetic_normalised_gain": "Normalized Gain",
        "mean_synthetic_retention": "Retention",
        "mean_latency": "Latency (ms)",
        "resource_normalised_utility": "Resource-Normalized Utility",
    }
    available = [field for field in fields if field in seed_metrics]
    main_rows: list[dict[str, object]] = []
    for condition, group in seed_metrics.groupby("condition"):
        row: dict[str, object] = {"Condition": condition}
        for field in available:
            values = group[field].dropna().astype(float).tolist()
            if not values:
                continue
            low, high = bootstrap_confidence_interval(
                values,
                bootstrap_seed,
                bootstrap_samples,
            )
            label = fields[field]
            row[label] = sum(values) / len(values)
            row[f"{label} 95% CI Low"] = low
            row[f"{label} 95% CI High"] = high
        main_rows.append(row)
    main = pd.DataFrame(main_rows)
    _write_formats(main, tables / "main_comparison")
    _write_formats(paired, tables / "ablation_comparisons")
    ablation_fields = {
        "mean_synthetic_normalised_gain": "Delta Gain",
        "mean_synthetic_retention": "Delta Retention",
        "mean_latency": "Delta Latency",
        "resource_normalised_utility": "Delta Utility",
    }
    if paired.empty or "metric" not in paired:
        ablation_effects = pd.DataFrame(columns=["Ablation", *ablation_fields.values()])
    else:
        ablation_effects = (
            paired.loc[paired.metric.isin(ablation_fields)]
            .pivot(index="comparison_condition", columns="metric", values="mean_difference")
            .reset_index()
            .rename(
                columns={"comparison_condition": "Ablation"}
                | {field: label for field, label in ablation_fields.items()}
            )
        )
    _write_formats(ablation_effects, tables / "ablation_effects")
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
    path_distribution = (
        pd.crosstab(
            interactions.condition,
            interactions.actual_adaptation_path,
            normalize="index",
        )
        .reset_index()
        .rename(columns={"condition": "Condition"})
    )
    _write_formats(path_distribution, tables / "path_distribution")
    publication_profiles = {
        name: profile
        for name, profile in PROFILES.items()
        if name
        in {
            "fast_learner",
            "slow_learner",
            "elevated_guess",
            "elevated_slip",
            "stronger_forgetting",
            "misconception_prone",
            "intermittent",
            "constrained_resource",
        }
    }
    profile_table = pd.DataFrame(
        [{"Profile": name, **asdict(profile)} for name, profile in publication_profiles.items()]
    )
    _write_formats(profile_table, tables / "synthetic_learner_profiles")
