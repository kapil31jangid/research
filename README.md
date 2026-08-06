# RAPID-Learn

RAPID-Learn (Resource-Aware, Personalised and Intelligent Dynamic Learning) is an offline-capable adaptive-learning research prototype for low-resource settings. It will personalise learning using learner knowledge, uncertainty, misconceptions, prerequisites, forgetting, and device constraints.

## Current status

Milestones 1–2 are implemented: a FastAPI and SQLite foundation, a validated fraction prerequisite graph, 12 seeded concepts, 100 seeded diagnostic/practice questions, and persisted BKT-ready learner concept state with independent uncertainty and dynamic forgetting estimates. Interaction-driven learner-state updates, recommendations, resource-aware policy, synchronisation, the frontend, ML, and experiments are intentionally future milestones.

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
