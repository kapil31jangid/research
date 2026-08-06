"""Run reproducible simulated controller comparisons; never real learner evaluation."""
import argparse, json, sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.evaluation.ablation import CONTROLLER_MODES
from app.evaluation.resource_metrics import personalisation_retention_ratio

EFFECT = {"static_curriculum": .00, "rule_based": .03, "bkt_only": .05, "ml_only": .04, "hybrid_no_resource": .07, "resource_aware_hybrid": .09, "resource_aware_no_uncertainty": .06, "resource_aware_no_misconception": .06, "resource_aware_no_forgetting": .06, "resource_aware_no_prerequisites": .05}
def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--controller", choices=CONTROLLER_MODES + ["all"], default="resource_aware_hybrid"); parser.add_argument("--learners", type=int, default=1000); parser.add_argument("--interactions", type=int, default=100); parser.add_argument("--resource-profile", choices=["low", "moderate", "high"], default="low"); parser.add_argument("--seed", type=int, default=42); parser.add_argument("--output", type=Path, default=Path("data/experiments/latest")); args = parser.parse_args(); rng = np.random.default_rng(args.seed); modes = CONTROLLER_MODES if args.controller == "all" else [args.controller]; resource = {"low": .45, "moderate": .70, "high": .92}[args.resource_profile]; rows = []
    for mode in modes:
        for learner in range(args.learners):
            baseline = rng.uniform(.15, .45); gain = np.clip(EFFECT[mode] + .04 * resource + rng.normal(0, .025), -.1, .25); latency = max(.2, {"static_curriculum": 1, "rule_based": 2, "bkt_only": 4, "ml_only": 9, "hybrid_no_resource": 5, "resource_aware_hybrid": 4}[mode] if mode in {"static_curriculum","rule_based","bkt_only","ml_only","hybrid_no_resource","resource_aware_hybrid"} else 4); rows.append({"mode": mode, "learner": learner, "learning_gain": gain, "accuracy": np.clip(baseline + gain, 0, 1), "latency_ms": latency + rng.normal(0,.2), "memory_mb": latency * 3 + rng.uniform(1,4), "cpu_percent": min(100, latency * 8 + rng.uniform(1,10)), "bandwidth_kb": 0 if resource < .5 else rng.uniform(1,5), "resource_score": resource})
    frame = pd.DataFrame(rows); summary = frame.groupby("mode", as_index=False).mean(numeric_only=True); full = summary.loc[summary["resource_score"].idxmax(), "accuracy"]; summary["personalisation_retention_ratio"] = summary["accuracy"].map(lambda value: personalisation_retention_ratio(value, full)); args.output.mkdir(parents=True, exist_ok=True); frame.to_csv(args.output / "learner_results.csv", index=False); summary.to_csv(args.output / "summary.csv", index=False); (args.output / "summary.json").write_text(json.dumps({"simulated": True, "configuration": vars(args) | {"output": str(args.output)}, "results": summary.to_dict(orient="records")}, indent=2), encoding="utf-8"); (args.output / "report.md").write_text("# Simulated RAPID-Learn experiment\n\nThese results are synthetic simulations, not real learner outcomes.\n\n" + summary.to_csv(index=False), encoding="utf-8")
    for column, title in [("learning_gain","Learning gain"),("accuracy","Accuracy"),("latency_ms","Latency (ms)"),("memory_mb","Memory (MB)"),("cpu_percent","CPU (%)"),("bandwidth_kb","Bandwidth (KB)"),("personalisation_retention_ratio","Personalisation retention")]:
        plt.figure(figsize=(7,4)); plt.bar(summary["mode"], summary[column]); plt.xticks(rotation=35, ha="right"); plt.title(f"Simulated {title}"); plt.tight_layout(); plt.savefig(args.output / f"{column}.png", dpi=150); plt.close()
    print(f"Wrote simulated experiment results to {args.output}")
if __name__ == "__main__": main()
