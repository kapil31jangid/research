# RAPID-Learn

RAPID-Learn (Resource-Aware, Personalised and Intelligent Dynamic Learning) is an
offline-capable adaptive-learning research prototype for low-resource settings. It
combines Bayesian Knowledge Tracing (BKT), learner uncertainty, retained mastery,
prerequisites, misconception evidence, offline-content availability, and device
resource signals in an explainable deterministic controller.

The project includes:

- a FastAPI and SQLite backend;
- a React progressive web application with an IndexedDB interaction queue;
- 24 concise, typed fraction lessons with visual models, worked examples, and
  checkpoints;
- explicit learning-activity metadata and lifecycle controls;
- an optional validated response-prediction model with safe BKT fallback;
- a deterministic synthetic learner and resource simulator;
- multi-condition, multi-seed ablation experiments;
- bootstrap statistics, CSV/Parquet exports, and publication-oriented plots and
  tables.

All current evaluation results are synthetic. They demonstrate software and
controller behavior, not real-world educational effectiveness.

## Requirements

- Python 3.12 or newer
- Node.js 22
- npm
- Docker with the Compose plugin, or Podman with a Compose provider

Run commands from the repository root.

## Local setup

Create the environment and install the backend and development dependencies:

```bash
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e '.[dev]'
npm ci --prefix frontend
```

Runtime settings have safe defaults. To customize them, copy the example file:

```bash
cp .env.example .env
```

The database is created, compatibility-checked, and seeded automatically when the
backend starts. It can also be initialized explicitly:

```bash
.venv/bin/python -m app.database.seed
```

## Run locally

Start the API in one terminal:

```bash
make backend
```

Start the PWA in another terminal:

```bash
make frontend
```

Open:

- PWA: <http://localhost:5173>
- API: <http://localhost:8000>
- OpenAPI documentation: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

Verify the API from a shell:

```bash
curl http://localhost:8000/health
```

### Alternative local ports

If both ports must change, keep the frontend API URL and backend CORS origin aligned:

```bash
# Terminal 1
RAPID_LEARN_BACKEND_PORT=8001 \
RAPID_LEARN_CORS_ORIGINS=http://localhost:5174 \
make backend

# Terminal 2
RAPID_LEARN_FRONTEND_PORT=5174 \
VITE_API_URL=http://localhost:8001 \
make frontend
```

## Run with containers

Docker:

```bash
docker compose up --build
```

Podman:

```bash
podman compose up --build
```

The containerized application uses the same URLs: frontend on port 5173 and API on
port 8000. Stop the stack while preserving the SQLite volume with:

```bash
docker compose down
# or
podman compose down
```

Delete the Compose volume and its local database only when a clean reset is intended:

```bash
docker compose down -v
# or
podman compose down -v
```

If only port 5173 is occupied, change the frontend host port and its allowed CORS
origin together:

```bash
RAPID_LEARN_FRONTEND_PORT=5174 \
RAPID_LEARN_CORS_ORIGINS=http://localhost:5174 \
docker compose up --build
```

The production frontend is currently built with `http://localhost:8000` as its
default API URL, so changing only the containerized backend host port is not
supported. Check port ownership before starting the stack:

```bash
ss -ltnp | grep -E ':(8000|5173)\b'
```

On systems where `docker` is unavailable, install Docker with its Compose plugin or
install Podman and a Podman Compose provider. A `podman-docker` compatibility package
may also expose Podman through the `docker` command.

## Validation commands

Run the same core checks used by CI:

```bash
.venv/bin/python -m pytest --cov=backend/app --cov-report=term-missing
.venv/bin/python -m ruff check backend
.venv/bin/python -m ruff format --check backend
npm ci --prefix frontend
npm run build --prefix frontend
docker compose build
```

With Podman, replace the final command with:

```bash
podman compose build
```

Convenience targets are also available:

```bash
make test
make lint
make seed
```

## Reproducible experiment harness

The evaluation harness uses isolated SQLite databases and the real interaction,
controller, BKT, misconception, offline-resolution, and recommendation code. The CLI
prints the generated artifact directory when a run completes.

### Single smoke run

```bash
.venv/bin/python -m app.evaluation.cli run \
  --config experiments/configs/smoke.json
```

### Multi-seed smoke ablation suite

```bash
.venv/bin/python -m app.evaluation.cli run-ablation-suite \
  --config experiments/configs/smoke.json \
  --seeds 11 22
```

The smoke configuration uses two learners, five interactions, and 200 bootstrap
samples. It intentionally uses misconception-heavy synthetic profiles to exercise
ID-level remediation behavior quickly.

### Run one configured condition across several seeds

```bash
.venv/bin/python -m app.evaluation.cli run-suite \
  --config experiments/configs/smoke.json \
  --seeds 11 22
```

`run-suite` repeats only the condition named in the configuration. In contrast,
`run-ablation-suite` runs the standard nine-condition matrix.

### Final synthetic study

The final configuration contains 500 learners, 40 interactions per learner, eight
isolated suite workers, and 10,000 bootstrap samples. Across nine conditions and five
seeds, the command simulates 900,000 interactions:

```bash
.venv/bin/python -m app.evaluation.cli run-ablation-suite \
  --config experiments/configs/final_study.json \
  --seeds 11 22 33 44 55 \
  --allow-large-run
```

`--allow-large-run` is intentionally required because this workload exceeds the
configuration's safety limit. Do not use it without reviewing learner, interaction,
condition, seed, disk, and runtime requirements.

### Read a run or suite summary

Replace the placeholder with the path printed by the preceding command:

```bash
.venv/bin/python -m app.evaluation.cli summarize \
  --experiment artifacts/experiments/<run-directory>

.venv/bin/python -m app.evaluation.cli summarize \
  --experiment artifacts/experiments/suites/<suite-directory>
```

Per-run artifacts include configuration and provenance JSON, interaction CSV and
Parquet, learner metrics, concept outcomes, plots, and tables. Multi-seed suites add:

- `seed_metrics.csv`;
- `aggregate_metrics.csv` with bootstrap confidence intervals;
- `paired_comparisons.csv` with matched-seed ablation comparisons;
- combined `interactions.parquet`;
- PNG/PDF figures;
- CSV/Markdown/LaTeX tables.

Synthetic misconception state is keyed by real misconception ID. Exports keep
`synthetic_true_misconception_id` separate from
`system_detected_misconception_id`, and remediation reduces intensity only for an
exact activity-to-misconception match.

## Synthetic data and optional ML model

Generate the standalone synthetic training dataset:

```bash
.venv/bin/python scripts/generate_synthetic_data.py \
  --learners 1000 \
  --interactions 50 \
  --seed 42 \
  --output data/synthetic
```

Train and evaluate the optional logistic-regression predictor:

```bash
.venv/bin/python scripts/train_response_predictor.py \
  --data data/synthetic/interactions.parquet \
  --model data/models/response_predictor.joblib \
  --metrics data/models/response_predictor_metrics.json
```

The runtime validates artifact type, version, preprocessing pipeline, feature order,
and validation inference before enabling ML recommendations. A missing, corrupt, or
incompatible artifact is non-fatal: requested ML recommendations fall back fully to
BKT and persist the fallback reason. Synthetic training does not validate predictive
quality for real learners.

## Legacy controller experiment scripts

The repository retains the earlier controller-focused simulator and exporter:

```bash
.venv/bin/python scripts/run_experiments.py \
  --controller all \
  --learners 1000 \
  --interactions 100 \
  --resource-profile low \
  --seed 42 \
  --output data/experiments/latest

.venv/bin/python scripts/export_results.py \
  --input data/experiments/latest/summary.csv \
  --output data/experiments/latest/export.md
```

For current research evaluation, prefer `app.evaluation.cli`, which records stronger
provenance, ID-level misconception state, multi-seed statistics, and publication
artifacts.

## Architecture and correctness notes

- `LearningActivity` is the recommendation source of truth for activity type,
  difficulty, supported paths, offline and bundled availability, computational cost,
  misconception links, and lifecycle state.
- Learner-facing lesson documents are separate, typed JSON content under
  `data/activities/fractions/`. Startup validates that every active seeded activity
  has matching content before serving requests.
- The PWA uses the backend recommendation as the sole source for its next lesson.
  Opened activity payloads are cached in IndexedDB by activity ID; when offline, the
  same typed payload is rendered and answer submissions remain in the existing sync
  queue.
- Inactive or deprecated activities remain readable in historical recommendations
  but cannot be recommended again.
- Misconception evidence is scoped to learner and concept, with validated evidence
  windows, minimum counts, and confidence thresholds.
- App-shell availability alone never implies that educational content is cached.
- Candidate-specific ML features use retained mastery, activity and concept
  difficulty, recent correctness, elapsed practice time, candidate prerequisites,
  learner history, and resource score.
- `selected_candidate_predicted_probability` is the canonical ML probability. The
  older interaction-level field remains only for compatibility and is not populated
  by current recommendation logic.
- Each interaction, learner-state update, mastery-history row, misconception update,
  recommendation, fallback metadata, and latency measurement commits atomically or
  rolls back together.
- Estimated computational cost is distinct from measured controller,
  recommendation, and total adaptive latency. Measured values vary by hardware.
- Existing SQLite databases receive documented additive compatibility updates at
  startup; no general migration framework is configured.

## Key API endpoints

- `GET /health`
- `POST /learners`, `GET /learners`, `GET /learners/{learner_id}`
- `GET /learners/{learner_id}/state`, `/progress`, `/learning-plan`
- `GET /concepts`, `GET /concepts/{concept_id}`, `GET /curriculum/graph`
- `GET /questions`, `GET /questions/next`, `GET /questions/{question_id}`
- `GET /activities/{activity_id}`, `GET /concepts/{concept_id}/activities`
- `POST /interactions`, `GET /interactions/{learner_id}`
- `POST /recommendations/generate`, `GET /recommendations/{learner_id}`
- `GET /resources/current`, `POST /resources/simulate`

See [API documentation](docs/api.md), [architecture](docs/architecture.md),
[research design](docs/research-design.md), and
[experiment methodology](docs/experiments.md).

## Limitations

- No classroom deployment or controlled learner study has been completed.
- Synthetic mastery gain is a simulation proxy, not causal evidence of learning.
- The optional model may be trained on synthetic data and requires validation on real
  learner data before educational interpretation.
- Activity and misconception metadata are prototype-curated.
- Runtime measurements depend on hardware and concurrent load.
- SQLite is intended for this single-device research prototype, not a production
  multi-user deployment.
- Offline PWA behavior depends on browser service-worker and storage support.

RAPID-Learn should currently be interpreted as a reproducible research software
prototype, not as a validated educational intervention.
