# RAPID-Learn

RAPID-Learn (Resource-Aware, Personalised and Intelligent Dynamic Learning) is an offline-capable adaptive-learning research prototype for low-resource settings. It personalises fraction learning using learner knowledge, uncertainty, misconceptions, prerequisites, forgetting, and device constraints.

## Current status

All ten planned milestones are implemented as a research prototype: adaptive backend, learner modelling, educational intelligence, resource-aware control, recommendations, PWA interface, synthetic ML pipeline, simulated experiments, and documentation/test hardening.

The system is ready for local and simulated studies. It is not validated for classroom deployment or real learner outcomes.

## Reliability notes

Misconception evidence is learner- and concept-scoped, with validated configurable evidence windows, minima, and thresholds. Cached recommendations require relevant seeded learning content; an app shell alone is insufficient. The optional ML artefact is validated lazily and prediction failures safely use BKT while retaining requested/actual-path metadata. Interactions persist atomically, and measured latency is hardware-dependent.

## Features

- Fraction prerequisite graph with 12 concepts and 100 seeded questions
- BKT mastery estimates, uncertainty, dynamic forgetting, and mastery history
- Data-driven misconception detection and prerequisite-aware diagnostic selection
- Resource monitoring/simulation with an explainable adaptation controller
- Persisted interaction loop, ranked recommendations, alternatives, and history
- Responsive React PWA with app-shell caching, offline indicator, and IndexedDB queue
- Optional logistic-regression response predictor trained from reproducible synthetic data
- Simulated controller baselines, ablations, metrics, CSV/JSON/Markdown exports, and charts

## Frontend and ML

Run the PWA with `make frontend`; it caches its app shell, displays offline and pending-sync status, and queues answer events in IndexedDB until connectivity returns. Generate simulated (not real learner) data with `python scripts/generate_synthetic_data.py`, then train the optional predictor with `python scripts/train_response_predictor.py`. The controller safely falls back to BKT when no model artifact is available.

No educational outcomes or device-performance claims have been validated with real learners. Seed content is prototype content for research development.

## Run commands

### One-time setup

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
npm --prefix frontend install
```

### Backend API

```bash
make backend
```

The API is available at `http://localhost:8000`; OpenAPI docs are at `http://localhost:8000/docs`.

### Frontend PWA

```bash
make frontend
```

Vite serves the frontend at `http://localhost:5173`.

### Full Docker stack

```bash
docker compose up --build
# Stop containers and remove the local Compose volume
docker compose down -v
```

If ports `8000` or `5173` are busy, choose alternative host ports:

```bash
RAPID_LEARN_BACKEND_PORT=8001 RAPID_LEARN_FRONTEND_PORT=5174 docker compose up --build
```

### Database seed

```bash
.venv/bin/python -m app.database.seed
```

### Backend tests, coverage, and lint

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check backend
.venv/bin/python -m ruff format --check backend
```

### Frontend production build

```bash
npm --prefix frontend run build
```

### Synthetic data and optional ML model

```bash
.venv/bin/python scripts/generate_synthetic_data.py --learners 1000 --interactions 50 --seed 42
.venv/bin/python scripts/train_response_predictor.py
```

### Simulated controller experiments

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

All generated results are explicitly simulated. They are research-development artifacts, not evidence of learning impact or device performance.

## Limitations

The prototype has not been validated with real learners or classroom deployments. Its local SQLite store is intentionally single-device; progressive multi-device synchronisation and authentication remain future work. Offline PWA caching covers the app shell and queued interactions, but does not replace formal service-worker background-sync support on every browser.

## Key endpoints

- `GET /health`
- `POST /learners`, `GET /learners`, `GET /learners/{learner_id}`
- `GET /learners/{learner_id}/state`, `/progress`, `/learning-plan`
- `GET /concepts`, `GET /concepts/{concept_id}`, `GET /curriculum/graph`
- `GET /questions`, `GET /questions/next`, `GET /questions/{question_id}`
- `POST /interactions`, `GET /interactions/{learner_id}`
- `POST /recommendations/generate`, `GET /recommendations/{learner_id}`
- `GET /resources/current`, `POST /resources/simulate`

See [docs/api.md](docs/api.md) and [docs/architecture.md](docs/architecture.md).
