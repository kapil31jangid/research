.PHONY: backend frontend test lint seed

backend:
	.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload

frontend:
	npm --prefix frontend run dev

test:
	.venv/bin/python -m pytest

lint:
	.venv/bin/python -m ruff check backend

seed:
	.venv/bin/python -m app.database.seed
