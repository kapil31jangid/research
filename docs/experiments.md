# Experiments

## Reproducible synthetic harness

The evaluation harness runs deterministic synthetic populations through the real
interaction service in an isolated SQLite database. It records a serialised config,
config hash, git/runtime provenance, interaction-level Parquet/CSV data, summaries,
tables, and plots under `artifacts/experiments/`. Run the smoke configuration with:

```bash
.venv/bin/python -m app.evaluation.cli run --config experiments/configs/smoke.json
```

Run multiple seeds or standard ablations with `run-suite` and
`run-ablation-suite`; all outputs are explicitly labelled `synthetic`. Synthetic
mastery and response outcomes are system-behaviour proxies, not evidence of classroom
effectiveness or causal learning gains.

The runtime receives an immutable evaluation policy. `full` enables every component.
Each `no_*` condition disables its named component at the real runtime boundary.
`bkt_only` retains BKT and adaptation but disables uncertainty, forgetting,
misconceptions, resource awareness, offline adaptation, and ML. `static_baseline`
disables every adaptive signal and follows a curriculum-order question/activity
sequence independent of learner state. Production requests omit this policy and keep
normal behaviour.

Interaction exports distinguish `system_mastery_*` (RAPID-Learn's estimate) from
`synthetic_*_mastery_*` (simulator latent state). Cross-concept recommendations update
only the selected concept's independent learning state. `concept_outcomes.csv` and
Parquet contain true pre-interaction and final values for every learner and concept;
primary mastery gain is computed from those multi-concept snapshots.

Multi-seed suites write seed metrics, bootstrap aggregate intervals, paired
full-versus-ablation comparisons and effect sizes, PNG/PDF plots, and
CSV/Markdown/LaTeX tables under `artifacts/experiments/suites/`. Candidate ML
probabilities are matched to the next observed assessment of the recommended concept,
so reported Brier, log-loss, ROC-AUC, accuracy and calibration are temporally aligned
synthetic diagnostics only.

```bash
.venv/bin/python -m app.evaluation.cli run-ablation-suite \
  --config experiments/configs/smoke.json --seeds 11 22
.venv/bin/python -m app.evaluation.cli summarize \
  --experiment artifacts/experiments/<run-or-suite>
```

The CLI refuses workloads beyond `max_interactions_without_override` unless
`--allow-large-run` is explicitly supplied. Run and suite metadata include config
hash, git revision, seed, environment, and integrity labels stating that results are
synthetic and educational effectiveness is not validated.

Offline analysis uses `offline_content_reason` with `matching_offline_activity_ids`,
not app-shell state alone. ML analysis uses
`selected_candidate_predicted_probability` and `candidate_prediction_summary`; the
learning-zone contribution targets the configurable success probability (0.70 by
default) and complements pedagogical need, uncertainty, prerequisites, repetition,
and resource cost.

The synthetic-data generator is implemented for Milestone 8. Run `python scripts/generate_synthetic_data.py` to create 1,000 simulated learners with 50 interactions each by default, plus CSV and Parquet outputs. Profiles include fast/slow learners, high guessing/slip, frequent forgetting, misconception-prone, intermittent, and low-resource users. Use `python scripts/train_response_predictor.py` to produce a versioned logistic-regression artifact and validation/test metrics.

These are simulated experiments only. They must not be interpreted as learning outcomes, field-study evidence, or validated performance claims.

Exported adaptive decisions distinguish estimated computational cost from controller, recommendation, and total adaptive latency. Timing excludes commit time and varies with hardware and runtime conditions.
