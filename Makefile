.PHONY: backend frontend test lint seed

RAPID_LEARN_BACKEND_PORT ?= 8000
RAPID_LEARN_FRONTEND_PORT ?= 5173

backend:
	.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --port $(RAPID_LEARN_BACKEND_PORT)

frontend:
	npm --prefix frontend run dev -- --port $(RAPID_LEARN_FRONTEND_PORT)

test:
	.venv/bin/python -m pytest

lint:
	.venv/bin/python -m ruff check backend

seed:
	.venv/bin/python -m app.database.seed
