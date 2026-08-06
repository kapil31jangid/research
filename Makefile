.PHONY: backend frontend test lint seed

backend:
	uvicorn app.main:app --app-dir backend --reload

frontend:
	npm --prefix frontend run dev

test:
	pytest

lint:
	ruff check backend

seed:
	python -m app.database.seed
