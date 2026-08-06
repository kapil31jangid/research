# RAPID-Learn

RAPID-Learn (Resource-Aware, Personalised and Intelligent Dynamic Learning) is an offline-capable adaptive-learning research prototype for low-resource settings. It will personalise learning using learner knowledge, uncertainty, misconceptions, prerequisites, forgetting, and device constraints.

## Current status

Milestones 1–8 are implemented: the adaptive backend, a responsive offline-capable React PWA, reproducible synthetic learner data, and an optional logistic-regression response predictor. Synchronisation, experiment baselines, and production hardening remain future milestones.

## Frontend and ML

Run the PWA with `make frontend`; it caches its app shell, displays offline and pending-sync status, and queues answer events in IndexedDB until connectivity returns. Generate simulated (not real learner) data with `python scripts/generate_synthetic_data.py`, then train the optional predictor with `python scripts/train_response_predictor.py`. The controller safely falls back to BKT when no model artifact is available.

No educational outcomes or device-performance claims have been validated with real learners. Seed content is prototype content for research development.

## Run locally

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
make backend
```

The API is available at `http://localhost:8000`; interactive OpenAPI docs are at `/docs`.

Or run the backend container:

```bash
docker compose up --build
```

## Test and lint

```bash
make test
make lint
```

## Initial endpoints

- `GET /health`
- `POST /learners`, `GET /learners`, `GET /learners/{learner_id}`
- `GET /concepts`, `GET /concepts/{concept_id}`, `GET /curriculum/graph`
- `GET /questions`, `GET /questions/{question_id}`

See [docs/api.md](docs/api.md) and [docs/architecture.md](docs/architecture.md).
