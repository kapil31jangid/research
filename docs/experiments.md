# Experiments

## Reproducible synthetic harness

The evaluation harness runs deterministic synthetic populations through the real
interaction service in an isolated SQLite database. It records a serialised config,
config hash, git/runtime provenance, interaction-level Parquet/CSV data, summaries,
tables, and plots under `artifacts/experiments/`. Run the smoke configuration with:

```bash
python -m app.evaluation.cli run --config experiments/configs/smoke.json
```

Run multiple seeds or standard ablations with `run-suite` and
`run-ablation-suite`; all outputs are explicitly labelled `synthetic`. Synthetic
mastery and response outcomes are system-behaviour proxies, not evidence of classroom
effectiveness or causal learning gains.

Offline analysis uses `offline_content_reason` with `matching_offline_activity_ids`,
not app-shell state alone. ML analysis uses
`selected_candidate_predicted_probability` and `candidate_prediction_summary`; the
learning-zone contribution targets the configurable success probability (0.70 by
default) and complements pedagogical need, uncertainty, prerequisites, repetition,
and resource cost.

The synthetic-data generator is implemented for Milestone 8. Run `python scripts/generate_synthetic_data.py` to create 1,000 simulated learners with 50 interactions each by default, plus CSV and Parquet outputs. Profiles include fast/slow learners, high guessing/slip, frequent forgetting, misconception-prone, intermittent, and low-resource users. Use `python scripts/train_response_predictor.py` to produce a versioned logistic-regression artifact and validation/test metrics.

These are simulated experiments only. They must not be interpreted as learning outcomes, field-study evidence, or validated performance claims.

Exported adaptive decisions distinguish estimated computational cost from controller, recommendation, and total adaptive latency. Timing excludes commit time and varies with hardware and runtime conditions.
