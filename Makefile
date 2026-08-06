.PHONY: backend test lint seed

backend:
	uvicorn app.main:app --app-dir backend --reload

test:
	pytest

lint:
	ruff check backend

seed:
	python -m app.database.seed

