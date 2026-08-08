"""Honest, publication-sized plots of simulated system behaviour."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def write_plots(interactions: pd.DataFrame, directory: Path) -> None:
    plots = directory / "plots"
    plots.mkdir(exist_ok=True)
    values = interactions.groupby("step", as_index=False).system_mastery_after.mean()
    figure, axis = plt.subplots(figsize=(6, 4))
    axis.plot(values.step, values.system_mastery_after)
    axis.set(
        title="Synthetic experiment: mean system mastery over interactions",
        xlabel="Interaction step",
        ylabel="Mean mastery",
    )
    for extension in ("png", "pdf"):
        figure.savefig(plots / f"mean_mastery.{extension}", bbox_inches="tight", dpi=160)
    plt.close(figure)


def _bar_plot(frame: pd.DataFrame, value: str, title: str, ylabel: str, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(7, 4))
    axis.bar(frame.condition, frame[value])
    axis.tick_params(axis="x", rotation=35)
    axis.set(title=title, xlabel="Condition", ylabel=ylabel)
    for extension in ("png", "pdf"):
        figure.savefig(path.with_suffix(f".{extension}"), bbox_inches="tight", dpi=160)
    plt.close(figure)


def write_suite_plots(
    seed_metrics: pd.DataFrame,
    paired: pd.DataFrame,
    interactions: pd.DataFrame,
    matched_predictions: pd.DataFrame,
    directory: Path,
) -> None:
    plots = directory / "plots"
    plots.mkdir(exist_ok=True)
    grouped = seed_metrics.groupby("condition", as_index=False).mean(numeric_only=True)
    figures = (
        ("mean_final_mastery", "Synthetic experiment: final system mastery", "Mastery"),
        ("mean_mastery_gain", "Synthetic experiment: system mastery gain", "Gain"),
        (
            "mean_synthetic_mastery_gain",
            "Synthetic experiment: latent mastery gain",
            "Latent gain",
        ),
        (
            "mastery_threshold_success_rate",
            "Synthetic experiment: mastery threshold success",
            "Rate",
        ),
        ("mean_latency", "Synthetic experiment: adaptive latency", "Milliseconds"),
        ("p95_latency", "Synthetic experiment: p95 adaptive latency", "Milliseconds"),
        (
            "misconception_resolution_rate",
            "Synthetic experiment: misconception resolution",
            "Resolution rate",
        ),
        (
            "mean_estimated_compute_cost_ms",
            "Synthetic experiment: estimated compute cost",
            "Milliseconds",
        ),
    )
    for field, title, ylabel in figures:
        if field in grouped:
            _bar_plot(grouped, field, title, ylabel, plots / field)
    if not paired.empty:
        for metric, filename in (
            ("mean_mastery_gain", "ablation_mastery_delta"),
            ("mean_latency", "ablation_latency_delta"),
            ("mean_estimated_compute_cost_ms", "ablation_compute_delta"),
        ):
            frame = paired.loc[paired.metric == metric].rename(
                columns={"comparison_condition": "condition", "mean_difference": metric}
            )
            if not frame.empty:
                _bar_plot(
                    frame,
                    metric,
                    f"Synthetic experiment: {metric} ablation difference",
                    "Full minus ablation",
                    plots / filename,
                )
    for group_field, filename, title in (
        (
            "condition",
            "adaptation_path_distribution",
            "Synthetic experiment: adaptation-path distribution",
        ),
        (
            "resource_profile",
            "adaptation_path_by_resource_profile",
            "Synthetic experiment: adaptation path by resource profile",
        ),
    ):
        distribution = pd.crosstab(
            interactions[group_field],
            interactions.actual_adaptation_path,
            normalize="index",
        )
        axis = distribution.plot(kind="bar", stacked=True, figsize=(8, 4)).axes
        axis.set(title=title, xlabel=group_field.replace("_", " "), ylabel="Share")
        figure = axis.figure
        for extension in ("png", "pdf"):
            figure.savefig(plots / f"{filename}.{extension}", bbox_inches="tight", dpi=160)
        plt.close(figure)
    for filename, kind in (
        ("ml_predicted_vs_observed", "scatter"),
        ("ml_calibration_curve", "calibration"),
        ("ml_probability_histogram", "histogram"),
    ):
        figure, axis = plt.subplots(figsize=(6, 4))
        if matched_predictions.empty:
            axis.text(0.5, 0.5, "No temporally matched ML samples", ha="center")
        elif kind == "scatter":
            axis.scatter(matched_predictions.probability, matched_predictions.outcome)
        elif kind == "histogram":
            axis.hist(matched_predictions.probability, bins=10)
        else:
            calibrated = (
                matched_predictions.assign(
                    bin=pd.cut(matched_predictions.probability, bins=10, include_lowest=True)
                )
                .groupby("bin", observed=True)
                .agg(probability=("probability", "mean"), outcome=("outcome", "mean"))
            )
            axis.plot(calibrated.probability, calibrated.outcome, marker="o")
            axis.plot([0, 1], [0, 1], linestyle="--", color="grey")
        axis.set(
            title=f"Synthetic experiment: {filename.replace('_', ' ')}",
            xlabel="Predicted probability",
            ylabel="Observed synthetic correctness",
        )
        for extension in ("png", "pdf"):
            figure.savefig(plots / f"{filename}.{extension}", bbox_inches="tight", dpi=160)
        plt.close(figure)
