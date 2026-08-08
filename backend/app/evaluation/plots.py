"""Honest, publication-sized plots of simulated system behaviour."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def write_plots(interactions: pd.DataFrame, directory: Path) -> None:
    plots = directory / "plots"
    plots.mkdir(exist_ok=True)
    values = interactions.groupby("step", as_index=False).mastery_after.mean()
    figure, axis = plt.subplots(figsize=(6, 4))
    axis.plot(values.step, values.mastery_after)
    axis.set(
        title="Synthetic mean mastery over interactions",
        xlabel="Interaction step",
        ylabel="Mean mastery",
    )
    for extension in ("png", "pdf"):
        figure.savefig(plots / f"mean_mastery.{extension}", bbox_inches="tight", dpi=160)
    plt.close(figure)
