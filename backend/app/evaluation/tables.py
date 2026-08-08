"""Portable CSV, Markdown, and LaTeX summaries for synthetic conditions."""

from pathlib import Path

import pandas as pd


def write_condition_table(interactions: pd.DataFrame, directory: Path) -> pd.DataFrame:
    grouped = interactions.groupby("condition", as_index=False).agg(
        Final_Mastery=("mastery_after", "mean"),
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
