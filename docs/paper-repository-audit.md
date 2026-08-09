# Paper-to-repository verification audit

This audit covers the manuscript *RAPID-Learn: A Resource-Aware Lightweight Adaptive
Learning Framework for Low-Resource Environments* and repository state used for the
final synthetic study. The manuscript was inspected but not modified.

All reported results are synthetic system-behaviour evidence. They are not classroom
outcomes, causal effects, or validation of educational effectiveness.

## Architecture map

| Component | Source | Verification | Paper requirement | Remaining qualification |
|---|---|---|---|---|
| HTTP and transaction pipeline | `backend/app/api`, `backend/app/services/interaction_service.py` | API, fresh-session, and rollback tests | Atomic observable interaction processing | SQLite remains a local prototype store |
| BKT | `backend/app/learner_model/bkt.py` | Equation/unit tests and runtime ablation | Concept-specific Bayesian update | Parameters are prototype-configured |
| Independent uncertainty | `backend/app/learner_model/uncertainty.py` | Unit and runtime-switch tests | Separate from mastery | Heuristic evidence model is not learner-validated |
| Retained mastery | `backend/app/learner_model/forgetting.py` | Elapsed-time and feature tests | Exponential decay at read time | Forgetting rates are synthetic assumptions |
| Prerequisite graph | `backend/app/curriculum/graph.py`, `prerequisites.py` | Graph, controller, and weakest-prerequisite tests | Block unsafe progression | Curriculum graph is curated prototype metadata |
| Misconceptions | `backend/app/misconceptions` | Concept-scope, evidence, and remediation tests | Repeated ID-level evidence | Rules are curated, not clinically validated |
| Resource scoring | `backend/app/resources/scoring.py` | Exact-formula and bounds tests | Equation (5), neutral missing battery | Synthetic snapshots are not device benchmarks |
| Adaptive controller | `backend/app/controller/policy.py` | Every deterministic path and priority tests | Auditable path selection | Fixed priorities are design choices |
| Candidate generation | `backend/app/recommendation/candidate_generator.py` | Activity, lifecycle, path, and relevance tests | Metadata-driven eligibility | Activity metadata is prototype-curated |
| Activity ranking | `backend/app/recommendation/scorer.py` | Exact configurable-weight test | Equation (6) | Runtime cost penalty is resource-adjusted |
| Offline resolution | `backend/app/offline/content_availability.py` | Resolver, persistence, app-shell, and PWA tests | Validate educational payloads | Availability reflects reported/bundled metadata |
| Optional logistic regression | `backend/app/ml_runtime`, `response_predictor.py` | Artifact-category, inference, ranking, and fallback tests | Optional candidate-level prediction | Synthetic model performs poorly on accepted study |
| Synthetic response model | `backend/app/evaluation/response_simulator.py` | Probability-direction and deterministic tests | Independent outcome generator | Parameters are heuristic assumptions |
| Simulator/system separation | `backend/app/evaluation/simulator.py`, `policy.py` | Independent-initial-state and runtime boundary tests | No latent-state leakage | Independence is implementation-level, not realism evidence |
| Conditions and ablations | `backend/app/evaluation/ablations.py` | Exact matrix and output path distributions | Nine runtime conditions | ML/offline controls are separate auxiliary suites |
| Multi-seed statistics | `backend/app/evaluation/suite.py`, `statistics.py` | Deterministic bootstrap and paired tests | Five seeds, matched comparisons | Five seed summaries give limited interval resolution |
| Outputs | `publication.py`, `plots.py`, `tables.py`, `paper_analysis.py` | Read-back and integrity audit | CSV/Parquet, tables, figures | Generated files are ignored by Git by design |
| PWA queue/cache | `frontend/src/offline/store.ts`, `LearningContext.tsx` | Real IndexedDB and reconnect tests | Cache content and synchronize queue | Browser storage quotas vary |

## Claim verification matrix

| Manuscript claim | Classification | Evidence |
|---|---|---|
| Bayesian Knowledge Tracing | VERIFIED BY IMPLEMENTATION | `learner_model/bkt.py`; learner-model tests |
| Independent learner uncertainty | VERIFIED BY IMPLEMENTATION | Separate persisted field, calculation, and `no_uncertainty` runtime switch |
| Retained mastery and forgetting | VERIFIED BY IMPLEMENTATION | Shared exponential retention utility and controlled-clock tests |
| Prerequisite graph and review | VERIFIED BY IMPLEMENTATION | Directed graph plus weakest-unmet-prerequisite selection tests |
| Concept-scoped misconception detection | VERIFIED BY IMPLEMENTATION | Learner+concept query, evidence thresholds, exact-ID remediation tests |
| Resource monitoring | VERIFIED BY IMPLEMENTATION | Host monitor and typed/simulated snapshots |
| Resource score equation | VERIFIED BY IMPLEMENTATION | Exact configured 0.35/0.25/0.20/0.20 formula test |
| Resource-aware controller | VERIFIED BY IMPLEMENTATION AND EXPERIMENT OUTPUT | Real runtime switch; identical exposure check; distinct path distributions |
| Metadata-driven candidate generation | VERIFIED BY IMPLEMENTATION | `LearningActivity` source, lifecycle/path/relevance tests |
| Activity ranking equation | VERIFIED BY IMPLEMENTATION | Configurable weighted scorer and exact-formula test |
| Offline educational-content availability | VERIFIED BY IMPLEMENTATION AND EXPERIMENT OUTPUT | App shell excluded; matching IDs/reasons persisted; offline metrics emitted |
| Optional logistic regression | VERIFIED BY IMPLEMENTATION AND EXPERIMENT OUTPUT | Versioned artifact 0.1.0; 5,216 ML selections in primary suite |
| Complete BKT fallback | VERIFIED BY IMPLEMENTATION | Fault-injection transaction test; no partial probabilities persisted |
| Independent synthetic latent state | VERIFIED BY IMPLEMENTATION | System initialization fixed at 0.20; latent state never enters controller input |
| Exactly nine primary conditions | VERIFIED BY EXPERIMENT OUTPUT | 45 runs: nine conditions by five seeds |
| 500 learners and 40 interactions | VERIFIED BY EXPERIMENT OUTPUT | Each condition-seed contains 20,000 rows and 500 learner IDs |
| Seeds 11, 22, 33, 44, 55 | VERIFIED BY EXPERIMENT OUTPUT | Suite manifest and every interaction row |
| 10,000 bootstrap resamples | VERIFIED BY EXPERIMENT OUTPUT | Config, suite metadata, and analysis provenance |
| 900,000 primary interactions | VERIFIED BY EXPERIMENT OUTPUT | 900,000 unique keys; CSV and Parquet counts agree |
| Section V metrics | VERIFIED BY IMPLEMENTATION AND EXPERIMENT OUTPUT | Definitions below and generated aggregate files |
| Section VI numeric results | NEEDS MANUSCRIPT REVISION | Manuscript contains placeholders; use accepted artifacts listed below |

No inspected technical claim is unsupported by both implementation and an explicit
qualification. Section VI must not claim Full RAPID-Learn dominates every baseline:
the accepted synthetic run does not support that statement.

## Exact nine-condition matrix

| Condition | BKT | Uncertainty | Forgetting | Prerequisites | Misconceptions | Resources | Offline | ML |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Static baseline | no | no | no | no | no | no | no | no |
| BKT only | yes | no | no | no | no | no | no | no |
| BKT + uncertainty | yes | yes | no | no | no | no | no | no |
| Pedagogical adaptive | yes | yes | yes | yes | yes | no | no | no |
| Full RAPID-Learn | yes | yes | yes | yes | yes | yes | yes | yes |
| No uncertainty | yes | no | yes | yes | yes | yes | yes | yes |
| No forgetting | yes | yes | no | yes | yes | yes | yes | yes |
| No misconceptions | yes | yes | yes | yes | no | yes | yes | yes |
| No resource awareness | yes | yes | yes | yes | yes | no | yes | yes |

`no_ml` and `no_offline_adaptation` are matched-seed auxiliary controls, not extra
members of the primary nine-condition design.

## Synthetic profile assumptions

These values are declared heuristic simulation parameters, not estimates of real
learners.

| Profile | Initial mastery | Learning rate | Guess | Slip | Forgetting | Misconception | Interruption | Resource | Offline |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| Fast learner | 0.65 | 0.10 | 0.08 | 0.05 | 0.02 | 0.08 | 0.03 | high-end | 0.02 |
| Slow learner | 0.30 | 0.04 | 0.08 | 0.12 | 0.04 | 0.12 | 0.08 | mid-range | 0.05 |
| Elevated guess | 0.35 | 0.07 | 0.28 | 0.08 | 0.03 | 0.10 | 0.05 | mid-range | 0.05 |
| Elevated slip | 0.50 | 0.07 | 0.05 | 0.25 | 0.03 | 0.10 | 0.05 | mid-range | 0.05 |
| Stronger forgetting | 0.50 | 0.07 | 0.08 | 0.10 | 0.12 | 0.10 | 0.12 | mid-range | 0.08 |
| Misconception-prone | 0.40 | 0.06 | 0.08 | 0.12 | 0.04 | 0.55 | 0.08 | mid-range | 0.08 |
| Intermittent | 0.45 | 0.06 | 0.08 | 0.10 | 0.06 | 0.12 | 0.45 | mixed | 0.25 |
| Constrained resource | 0.45 | 0.06 | 0.08 | 0.12 | 0.05 | 0.12 | 0.15 | low-end | 0.35 |

The machine-readable source is `results/paper_full/config/synthetic_profiles.json`.

## Metric definitions

| Metric | Formula | Source | Unit/aggregation | Edge case and test |
|---|---|---|---|---|
| Response accuracy | mean of correctness indicators | Observed synthetic responses after answer evaluation | proportion; learner/run/seed | Empty utility returns 0; exact test |
| System mastery gain | final mean system mastery minus initial mean | All learner-concept states | probability points per learner, then mean | Uses every scoped concept |
| Synthetic normalized gain | mean over concepts of `(post-pre)/max(1-pre, 1e-9)` | Independent latent pre/post concept state | ratio per learner, then seed mean | Protected denominator; exact test |
| Retention | mean `synthetic_retained_mastery / max(synthetic_mastery, 1e-9)`, capped at 1 | Simulator latent state before assessment | ratio per learner, then seed mean | Zero-safe; controlled elapsed time |
| Time to mastery | first 1-based interaction where mean system mastery reaches configured threshold | System state history | interactions; median among learners reaching threshold | Missing when never reached |
| Prerequisite violation | unmet prerequisite and neither prerequisite path nor selected unmet concept | Graph plus recommendation | conditional rate over gap events | Undefined if no gap |
| Misconception resolution | exact-ID intensity crosses configured threshold downward | Simulator-only misconception state | resolved/triggered event rate | Undefined with no triggers |
| Resource score | `0.35M + 0.25C + 0.20B + 0.20N` | Typed resource snapshot | bounded 0–1 | Missing battery contributes neutral 0.5; exact test |
| Resource-normalized utility | normalized gain divided by `1 +` weighted bounded latency, memory pressure, CPU, and bandwidth index | Learner and system metrics | dimensionless learner mean | Reference scales documented in code; zero-safe |
| Offline recommendation availability | mean validated content availability for interactions with network unavailable | Resolver output, not app shell | conditional proportion | Undefined when no offline interactions |
| Controller latency | controller decision boundary only | monotonic clock | ms, seed mean | Non-negative; hardware dependent |
| Recommendation latency | candidate generation, prediction/fallback, scoring, selection | monotonic clock | ms, seed mean | Non-negative; hardware dependent |
| Total adaptive latency | learner-state processing through recommendation preparation, excluding commit | monotonic clock | ms, p50/p95/p99 | Must contain nested phase timings |
| Memory | total minus available memory | resource snapshot | MB, seed mean | Bounded by simulated total |
| CPU | sampled CPU utilization | resource snapshot | percent, seed mean | Bounded 0–100 |
| Bandwidth | zero offline, otherwise selected activity size | activity metadata and network state | KB per interaction | Prototype content-size estimate |
| Brier score | mean `(p-y)^2` | prediction matched to next assessment of selected concept | probability score | Only temporally matched ML rows |
| Log loss | negative Bernoulli log likelihood with probabilities clipped to `[1e-12,1-1e-12]` | matched ML outcomes | loss | Only temporally matched rows |
| ROC-AUC | pairwise positive-versus-negative probability ordering | matched ML outcomes | 0–1 | Null unless both classes exist |
| Calibration error | ten-bin weighted absolute confidence-outcome difference | matched ML outcomes | 0–1 | Empty bins ignored |

Confidence intervals use 10,000 percentile-bootstrap resamples of five independent
condition-level seed summaries. Paired comparisons resample the five within-seed
Full-minus-comparison differences. Interaction rows are not bootstrapped as though
they were independent.

## Accepted and rejected runs

Accepted primary raw code revision: `e5995ad3b26fb434c6ac8409b0f4b62a01c76ad3`.
Accepted primary config hash: `e1fc14f5145f`. Analysis provenance records the later
analysis-code revision separately.

Two earlier complete datasets are retained under `results/rejected/` and excluded:

- `clock_leak_8a30c067ea50`: candidate ML features used wall-clock elapsed time;
- `resource_exposure_confounded_8c4a64e75fd1`: the resource ablation changed the
  simulated exposure instead of only disabling controller use.

The accepted dataset fixes both defects. Full and No-Resource-Awareness have exactly
matching memory, CPU, network, and resource-profile sequences for the same
seed/learner/step.

## Result interpretation constraints

- Full achieved higher response accuracy and retention than Static, but lower
  synthetic normalized gain. This mixed outcome must be reported.
- Removing misconception handling reduced response accuracy but produced higher
  synthetic mastery gain; the simulator rewards concept-match learning and targeted
  remediation changes activity allocation. Neither direction is classroom evidence.
- Full-versus-No-Resource-Awareness learning differences are near zero. Resource
  awareness changes feasibility/path behavior, but this run does not support a strong
  synthetic learning-gain claim for it.
- Only 32 of 900,000 primary interactions selected the cached path. Valid offline
  educational content was available for about one quarter of offline interactions;
  higher-priority pedagogical paths usually prevailed.
- Full selected ML for 5,216 interactions. Synthetic calibration was poor and the
  matched No-ML learning differences include zero. The model adds no demonstrated
  educational value in this study.
- Auxiliary suites were scheduled separately from the primary suite. Their learning
  metrics are matched by seed, but raw latency differences are descriptive hardware
  observations, not isolated component overhead.

## Paper-facing artifacts

The authoritative paths are under `results/paper_full/`:

- `raw/interactions.parquet` and `.csv`: 900,000 interaction rows;
- `raw/learner_metrics.csv`, `raw/concept_metrics.csv`;
- `aggregate/paper_ready_results.csv`: means and 95% intervals;
- `aggregate/paired_comparisons.csv`: primary matched-seed comparisons;
- `aggregate/ml_incremental_comparison.csv` and
  `offline_ablation_comparison.csv`: auxiliary controls;
- `aggregate/weight_sensitivity.csv`;
- `tables/paper_table_1_overall.{csv,md,tex}`;
- `tables/paper_table_2_ablation.{csv,md,tex}`;
- `tables/synthetic_learner_profiles.{csv,md,tex}`;
- `tables/weight_sensitivity.{csv,md,tex}`;
- `plots/figure_4_normalized_gain.{csv,png,pdf}`;
- `plots/figure_5_resource_performance.{csv,png,pdf}`;
- `metadata/final_integrity_audit.json` and `analysis_provenance.json`;
- `aggregate/paper_ready_findings.md`.

The manuscript's placeholder Table I, Figures 4–5, and Section VI text should be
updated from these files in a separate manuscript-editing task.
