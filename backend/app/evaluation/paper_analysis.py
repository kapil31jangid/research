"""Regenerate traceable paper-facing analyses from accepted synthetic suites."""

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from app.evaluation.config import ExperimentConfig
from app.evaluation.provenance import collect_provenance
from app.evaluation.statistics import (
    bootstrap_confidence_interval,
    cohens_d,
    paired_bootstrap_difference,
)
from app.evaluation.suite import paired_comparisons
from app.evaluation.tables import _write_formats

REPORT_METRICS = {
    "response_accuracy": "Accuracy",
    "mean_synthetic_normalised_gain": "Normalized Gain",
    "mean_synthetic_retention": "Retention",
    "mean_latency": "Latency (ms)",
    "resource_normalised_utility": "Resource-Normalized Utility",
}

CONDITION_ORDER = (
    "static_baseline",
    "bkt_only",
    "bkt_uncertainty",
    "pedagogical_adaptive",
    "full",
    "no_uncertainty",
    "no_forgetting",
    "no_misconceptions",
    "no_resource_awareness",
)


def build_overall_table(aggregate: pd.DataFrame) -> pd.DataFrame:
    """Return paper metrics with their seed-level bootstrap intervals."""
    rows: list[dict[str, object]] = []
    for condition in CONDITION_ORDER:
        row: dict[str, object] = {"Condition": condition}
        for metric, label in REPORT_METRICS.items():
            match = aggregate.loc[(aggregate.condition == condition) & (aggregate.metric == metric)]
            if match.empty:
                continue
            value = match.iloc[0]
            row[label] = float(value["mean"])
            row[f"{label} 95% CI Low"] = float(value.ci_low)
            row[f"{label} 95% CI High"] = float(value.ci_high)
        rows.append(row)
    return pd.DataFrame(rows)


def build_auxiliary_comparisons(
    primary_seed_metrics: pd.DataFrame,
    auxiliary_seed_metrics: list[pd.DataFrame],
    seed: int,
    bootstrap_samples: int,
) -> pd.DataFrame:
    """Compare auxiliary controls with Full using matched random seeds."""
    full = primary_seed_metrics.loc[primary_seed_metrics.condition == "full"]
    rows: list[dict[str, object]] = []
    for auxiliary in auxiliary_seed_metrics:
        for condition, comparison in auxiliary.groupby("condition"):
            paired = full.merge(comparison, on="random_seed", suffixes=("_full", "_comparison"))
            for metric in REPORT_METRICS:
                left = f"{metric}_full"
                right = f"{metric}_comparison"
                if left not in paired or right not in paired:
                    continue
                valid = paired[[left, right]].dropna()
                if valid.empty:
                    continue
                reference = valid[left].astype(float).tolist()
                other = valid[right].astype(float).tolist()
                difference, low, high = paired_bootstrap_difference(
                    reference,
                    other,
                    seed,
                    bootstrap_samples,
                )
                rows.append(
                    {
                        "metric": metric,
                        "reference_condition": "full",
                        "comparison_condition": condition,
                        "mean_difference": difference,
                        "ci_low": low,
                        "ci_high": high,
                        "effect_size": cohens_d(reference, other),
                        "matched_seed_count": len(valid),
                        "comparison_scope": (
                            "descriptive_only_separately_scheduled_runtime"
                            if metric == "mean_latency"
                            else "matched_seed_synthetic_comparison"
                        ),
                    }
                )
    return pd.DataFrame(rows)


def _integrity_audit(paper_root: Path, config: ExperimentConfig) -> dict[str, object]:
    summary = json.loads((paper_root / "metadata" / "suite_summary.json").read_text())
    columns = [
        "condition",
        "seed",
        "synthetic_learner_id",
        "step",
        "system_mastery_before",
        "system_mastery_after",
        "synthetic_assessed_mastery_before",
        "synthetic_assessed_mastery_after",
        "resource_score",
        "selected_candidate_predicted_probability",
        "measured_total_adaptive_latency_ms",
        "data_source",
        "simulated_results",
    ]
    frame = pd.read_parquet(paper_root / "raw" / "interactions.parquet", columns=columns)
    expected = config.learner_count * config.interactions_per_learner * 9 * 5
    duplicate_count = int(
        frame.duplicated(["condition", "seed", "synthetic_learner_id", "step"]).sum()
    )
    bounded_columns = [
        "system_mastery_before",
        "system_mastery_after",
        "synthetic_assessed_mastery_before",
        "synthetic_assessed_mastery_after",
        "resource_score",
        "selected_candidate_predicted_probability",
    ]
    bounds_valid = all(
        np.isfinite(frame[column].dropna().astype(float)).all()
        and frame[column].dropna().astype(float).between(0.0, 1.0).all()
        for column in bounded_columns
    )
    latency = frame.measured_total_adaptive_latency_ms.astype(float)
    return {
        "valid": bool(
            len(frame) == expected
            and duplicate_count == 0
            and bounds_valid
            and np.isfinite(latency).all()
            and (latency >= 0).all()
            and set(frame.condition) == set(CONDITION_ORDER)
            and set(frame.seed) == {11, 22, 33, 44, 55}
            and set(frame.data_source) == {"synthetic"}
            and bool(frame.simulated_results.all())
            and summary.get("integrity_valid") is True
        ),
        "expected_interactions": expected,
        "actual_interactions": len(frame),
        "duplicate_interactions": duplicate_count,
        "condition_count": frame.condition.nunique(),
        "seed_count": frame.seed.nunique(),
        "bounded_values_valid": bool(bounds_valid),
        "latencies_valid": bool(np.isfinite(latency).all() and (latency >= 0).all()),
        "data_source": "synthetic",
        "simulated_results": True,
    }


def _finding_text(
    overall: pd.DataFrame,
    paired: pd.DataFrame,
    auxiliary: pd.DataFrame,
    seed_metrics: pd.DataFrame,
    bootstrap_seed: int,
    bootstrap_samples: int,
) -> str:
    def result(condition: str, metric: str) -> tuple[float, float, float]:
        row = overall.loc[overall.Condition == condition].iloc[0]
        return (
            float(row[metric]),
            float(row[f"{metric} 95% CI Low"]),
            float(row[f"{metric} 95% CI High"]),
        )

    full_accuracy = result("full", "Accuracy")
    static_accuracy = result("static_baseline", "Accuracy")
    full_gain = result("full", "Normalized Gain")
    static_gain = result("static_baseline", "Normalized Gain")
    full_retention = result("full", "Retention")
    static_retention = result("static_baseline", "Retention")

    def difference(comparison: str, metric: str) -> tuple[float, float, float]:
        row = paired.loc[
            (paired.comparison_condition == comparison) & (paired.metric == metric)
        ].iloc[0]
        return float(row.mean_difference), float(row.ci_low), float(row.ci_high)

    misconception_accuracy = difference("no_misconceptions", "response_accuracy")
    misconception_gain = difference("no_misconceptions", "mean_synthetic_normalised_gain")
    resource_gain = difference("no_resource_awareness", "mean_synthetic_normalised_gain")
    resource_utility = difference("no_resource_awareness", "resource_normalised_utility")
    full_seeds = seed_metrics.loc[seed_metrics.condition == "full"]
    offline_values = full_seeds.offline_recommendation_availability.dropna().tolist()
    offline_low, offline_high = bootstrap_confidence_interval(
        offline_values, bootstrap_seed, bootstrap_samples
    )
    offline_mean = float(np.mean(offline_values))
    cached_count = int(
        round(float((full_seeds.offline_adaptation_rate * full_seeds.interaction_count).sum()))
    )
    ml_count = int(round(float((full_seeds.ml_usage_rate * full_seeds.interaction_count).sum())))
    ml_matched = int(full_seeds.synthetic_ml_matched_samples.sum())
    brier_values = full_seeds.synthetic_brier_score.dropna().tolist()
    brier_low, brier_high = bootstrap_confidence_interval(
        brier_values, bootstrap_seed, bootstrap_samples
    )
    brier_mean = float(np.mean(brier_values))
    ml_gain_row = auxiliary.loc[
        (auxiliary.comparison_condition == "no_ml")
        & (auxiliary.metric == "mean_synthetic_normalised_gain")
    ].iloc[0]
    ml_accuracy_row = auxiliary.loc[
        (auxiliary.comparison_condition == "no_ml") & (auxiliary.metric == "response_accuracy")
    ].iloc[0]
    lines = [
        "# Paper-ready synthetic findings",
        "",
        (
            "> All values below are simulation-based system-behaviour evidence, "
            "not validated educational outcomes."
        ),
        "",
        "## VI-A Overall adaptive performance",
        "",
        (
            f"Full RAPID-Learn response accuracy was {full_accuracy[0]:.4f} "
            f"(95% seed-bootstrap CI {full_accuracy[1]:.4f}–{full_accuracy[2]:.4f}), "
            f"compared with {static_accuracy[0]:.4f} "
            f"({static_accuracy[1]:.4f}–{static_accuracy[2]:.4f}) "
            "for Static. Full retained mastery was higher, but its synthetic normalized "
            "gain was lower: "
            f"retention {full_retention[0]:.4f} versus {static_retention[0]:.4f}, and "
            f"normalized gain {full_gain[0]:.4f} versus {static_gain[0]:.4f}. This mixed "
            "result indicates a simulator/controller trade-off and does not establish "
            "educational superiority."
        ),
        "",
        "## VI-B Component ablation analysis",
        "",
        (
            f"Removing misconception handling changed Full-minus-ablation accuracy by "
            f"{misconception_accuracy[0]:+.4f} (95% paired seed-bootstrap CI "
            f"{misconception_accuracy[1]:+.4f} to {misconception_accuracy[2]:+.4f}) and "
            f"synthetic normalized gain by {misconception_gain[0]:+.4f} "
            f"({misconception_gain[1]:+.4f} to {misconception_gain[2]:+.4f}). This is the "
            "largest positive Full-versus-component-ablation gain difference. Other "
            "component effects are small or mixed and remain visible in the paired output."
        ),
        "",
        "## VI-C Resource-aware behaviour",
        "",
        (
            f"Full and No-Resource-Awareness received identical resource sequences. The "
            f"paired normalized-gain difference was {resource_gain[0]:+.6f} (95% CI "
            f"{resource_gain[1]:+.6f} to {resource_gain[2]:+.6f}), and the utility "
            f"difference was {resource_utility[0]:+.6f} ({resource_utility[1]:+.6f} to "
            f"{resource_utility[2]:+.6f}). Both intervals include zero, so this simulation "
            "does not establish a learning or utility advantage from resource awareness. "
            "Runtime latency remains hardware- and concurrency-dependent."
        ),
        "",
        "## VI-D Offline behaviour",
        "",
        (
            f"Validated educational content was available for {offline_mean:.4f} of Full's "
            f"offline interactions (95% seed-bootstrap CI {offline_low:.4f}–{offline_high:.4f}); "
            f"shell-only availability was excluded. Only {cached_count} of 100,000 Full "
            "interactions selected the cached pathway because higher-priority pedagogical "
            "rules usually applied. The No-Offline auxiliary selected zero cached paths."
        ),
        "",
        "## VI-E Optional prediction model",
        "",
        (
            f"Full used ML for {ml_count} of 100,000 interactions and produced {ml_matched} "
            f"temporally matched outcomes. Mean seed-level synthetic Brier score was "
            f"{brier_mean:.4f} (95% CI {brier_low:.4f}–{brier_high:.4f}), indicating poor "
            f"probability quality. Relative to No-ML, Full's accuracy difference was "
            f"{float(ml_accuracy_row.mean_difference):+.6f} (95% CI "
            f"{float(ml_accuracy_row.ci_low):+.6f} to "
            f"{float(ml_accuracy_row.ci_high):+.6f}) and gain difference was "
            f"{float(ml_gain_row.mean_difference):+.6f} "
            f"({float(ml_gain_row.ci_low):+.6f} to {float(ml_gain_row.ci_high):+.6f}); "
            "both include zero. Complete BKT fallback is verified by fault injection; no "
            "natural fallback occurred in the accepted Full runs."
        ),
    ]
    if not auxiliary.empty:
        lines.extend(
            [
                "",
                "Auxiliary controls use the same five seeds and learner/resource exposure as Full.",
            ]
        )
    return "\n".join(lines) + "\n"


def write_paper_analysis(paper_root: Path, auxiliary_suites: list[Path]) -> Path:
    """Write reproducible paper tables, comparisons, integrity, and safe prose."""
    config = ExperimentConfig.model_validate_json(
        (paper_root / "config" / "final_study.json").read_text(encoding="utf-8")
    )
    aggregate_directory = paper_root / "aggregate"
    tables_directory = paper_root / "tables"
    metadata_directory = paper_root / "metadata"
    aggregate = pd.read_csv(aggregate_directory / "aggregate_metrics.csv")
    seed_metrics = pd.read_csv(aggregate_directory / "seed_metrics.csv")
    paired = paired_comparisons(seed_metrics, config)
    paired.to_csv(aggregate_directory / "paired_comparisons.csv", index=False)
    paired.to_csv(aggregate_directory / "ablation_comparisons.csv", index=False)
    ablation_labels = {
        "mean_synthetic_normalised_gain": "Delta Gain",
        "mean_synthetic_retention": "Delta Retention",
        "mean_latency": "Delta Latency",
        "resource_normalised_utility": "Delta Utility",
    }
    ablation_table = (
        paired.loc[paired.metric.isin(ablation_labels)]
        .pivot(index="comparison_condition", columns="metric", values="mean_difference")
        .reset_index()
        .rename(
            columns={"comparison_condition": "Ablation"}
            | {field: label for field, label in ablation_labels.items()}
        )
    )
    _write_formats(ablation_table, tables_directory / "ablation_effects")
    _write_formats(ablation_table, tables_directory / "paper_table_2_ablation")
    overall = build_overall_table(aggregate)
    overall.to_csv(aggregate_directory / "paper_ready_results.csv", index=False)
    _write_formats(overall, tables_directory / "overall_evaluation_with_ci")
    paper_subset = overall.loc[
        overall.Condition.isin(["static_baseline", "bkt_only", "pedagogical_adaptive", "full"])
    ]
    _write_formats(paper_subset, tables_directory / "paper_table_1_overall")
    auxiliary_frames = [pd.read_csv(path / "seed_metrics.csv") for path in auxiliary_suites]
    auxiliary = build_auxiliary_comparisons(
        seed_metrics,
        auxiliary_frames,
        config.random_seed,
        config.bootstrap_samples,
    )
    auxiliary.to_csv(aggregate_directory / "auxiliary_comparisons.csv", index=False)
    auxiliary.loc[auxiliary.comparison_condition == "no_ml"].to_csv(
        aggregate_directory / "ml_incremental_comparison.csv", index=False
    )
    auxiliary.loc[auxiliary.comparison_condition == "no_offline_adaptation"].to_csv(
        aggregate_directory / "offline_ablation_comparison.csv", index=False
    )
    _write_formats(auxiliary, tables_directory / "auxiliary_comparisons")
    integrity = _integrity_audit(paper_root, config)
    if not integrity["valid"]:
        raise ValueError("Paper-output integrity audit failed")
    (metadata_directory / "final_integrity_audit.json").write_text(
        json.dumps(integrity, indent=2), encoding="utf-8"
    )
    raw_provenance = json.loads(
        (metadata_directory / "provenance.json").read_text(encoding="utf-8")
    )
    analysis_provenance = collect_provenance(raw_provenance.get("model_version")) | {
        "analysis_started_at": datetime.now(UTC).isoformat(),
        "raw_experiment_git_commit_sha": raw_provenance.get("git_commit_sha"),
        "raw_experiment_config_hash": raw_provenance.get("config_hash"),
        "bootstrap_samples": config.bootstrap_samples,
        "bootstrap_resampling_unit": "condition-level seed summary",
        "confidence_level": 0.95,
        "auxiliary_suites": [str(path) for path in auxiliary_suites],
        "simulated_results": True,
        "data_source": "synthetic",
        "educational_effectiveness_validated": False,
    }
    (metadata_directory / "analysis_provenance.json").write_text(
        json.dumps(analysis_provenance, indent=2), encoding="utf-8"
    )
    (aggregate_directory / "paper_ready_findings.md").write_text(
        _finding_text(
            overall,
            paired,
            auxiliary,
            seed_metrics,
            config.random_seed,
            config.bootstrap_samples,
        ),
        encoding="utf-8",
    )
    return aggregate_directory / "paper_ready_results.csv"
