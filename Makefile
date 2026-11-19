.PHONY: setup models up down test lint eval
setup:
	python3.11 -m venv .venv && . .venv/bin/activate && pip install -e '.[dev,speech]'
models:
	./scripts/download_models.sh
up:
	test -f .env || cp .env.example .env
	docker compose up --build
down:
	docker compose down
test:
	pytest -q
lint:
	ruff check .
eval:
	python scripts/evaluate.py
