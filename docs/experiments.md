# Experiments

Experiment configurations carry `board_id`, `class_level`, `subject_id`,
`curriculum_pack_id`, and `curriculum_pack_version`. Defaults intentionally select
the legacy-compatible NCERT Class 5 Mathematics pack; changing packs requires an
explicit available pathway and keeps condition runs isolated.

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

`bootstrap_samples` is part of the typed experiment configuration and is recorded in
run and suite provenance. The smoke configuration uses 200 resamples to keep
verification quick; `final_study.json` uses 10,000 resamples for aggregate and paired
intervals.
Independent condition/seed databases can be executed concurrently using the recorded
`suite_workers` setting. Smoke and CI keep the default of one; the final eight-core
study configuration uses eight workers without sharing database state.

```bash
.venv/bin/python -m app.evaluation.cli run-ablation-suite \
  --config experiments/configs/smoke.json --seeds 11 22
.venv/bin/python -m app.evaluation.cli summarize \
  --experiment artifacts/experiments/<run-or-suite>
```

The documented serious synthetic study uses 500 learners, 40 interactions, seeds
11/22/33/44/55, and the nine standard conditions. It exceeds the normal workload
guard intentionally:

```bash
.venv/bin/python -m app.evaluation.cli run-ablation-suite \
  --config experiments/configs/final_study.json \
  --seeds 11 22 33 44 55 \
  --allow-large-run
```

After the primary suite and the two matched-seed auxiliary controls have completed,
regenerate the integrity audit, confidence-interval tables, safe paper text, and
incremental ML/offline comparisons with:

```bash
.venv/bin/python -m app.evaluation.cli analyze-paper \
  --experiment results/paper_full \
  --auxiliary-suites \
    results/paper_full/auxiliary_runs/suites/<no-ml-suite> \
    results/paper_full/auxiliary_runs/suites/<no-offline-suite>
```

The primary bootstrap resampling unit is the independent condition-level seed
summary. Paired comparisons use Full-minus-comparison differences for matching seeds;
they do not incorrectly treat 900,000 dependent interaction rows as independent.
See [the paper/repository audit](paper-repository-audit.md) for formulas, accepted
provenance, rejected runs, and interpretation constraints.

Synthetic misconception ground truth is keyed by the real rule identifier, not by
concept. A response records the selected synthetic misconception independently from
the system detector. Remediation reduces an intensity only when the selected activity
declares that exact identifier; resolution is the per-ID crossing from at or above
the configured threshold to below it. Exports distinguish
`synthetic_true_misconception_id` from `system_detected_misconception_id` and report
matched and unmatched remediation counts with safe denominators.

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
