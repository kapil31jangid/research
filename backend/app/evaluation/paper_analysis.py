"""Regenerate traceable paper-facing analyses from accepted synthetic suites."""

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from app.evaluation.config import ExperimentConfig
from app.evaluation.provenance import collect_provenance
from app.evaluation.statistics import cohens_d, paired_bootstrap_difference
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


def _finding_text(overall: pd.DataFrame, auxiliary: pd.DataFrame) -> str:
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
        f"Full RAPID-Learn response accuracy was {full_accuracy[0]:.4f} "
        f"(95% seed-bootstrap CI {full_accuracy[1]:.4f}–{full_accuracy[2]:.4f}), compared "
        f"with {static_accuracy[0]:.4f} ({static_accuracy[1]:.4f}–{static_accuracy[2]:.4f}) "(
            "for Static. Full retained mastery was higher, but its synthetic normalized "
            "gain was lower: "
        ),
        f"retention {full_retention[0]:.4f} versus {static_retention[0]:.4f}, and normalized gain "
        f"{full_gain[0]:.4f} versus {static_gain[0]:.4f}. This mixed result indicates a "
        "simulator/controller trade-off and does not establish educational superiority.",
        "",
        "## VI-B Component ablation analysis",
        "",
        "Use `aggregate/paired_comparisons.csv` for matched-seed Full-minus-ablation estimates. "(
            "Signs are retained even when an ablation is neutral or better; no unfavorable "
            "result is removed."
        ),
        "",
        "## VI-C Resource-aware behaviour",
        "",
        "Full and No-Resource-Awareness received identical simulated resource sequences. Their "
        "differences therefore measure controller use of resources rather than different exposure. "
        "Measured latency remains hardware- and concurrency-dependent.",
        "",
        "## VI-D Offline behaviour",
        "",
        (
            "Offline availability counts validated educational payloads only; "
            "application-shell caching "
        ),
        "is excluded. The dedicated No-Offline auxiliary comparison is stored in "
        "`aggregate/offline_ablation_comparison.csv`.",
        "",
        "## VI-E Optional prediction model",
        "",
        (
            "Candidate prediction diagnostics are synthetic and temporally aligned to the "
            "next observed "
        ),
        "response for the selected concept. The dedicated No-ML comparison is stored in "(
            "`aggregate/ml_incremental_comparison.csv`; fallback correctness is established "
            "by fault-injection "
        ),
        "tests, not by claiming a naturally occurring failure in the accepted full run.",
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
        _finding_text(overall, auxiliary), encoding="utf-8"
    )
    return aggregate_directory / "paper_ready_results.csv"
