.PHONY: install test lint ingest clean docker docker-ingest app

install:
	uv sync
	uv pip install -e .

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check src/ tests/

ingest:
	uv run python -m clinical_trial_pipeline.cli ingest --max-studies 100

ingest-full:
	uv run python -m clinical_trial_pipeline.cli ingest --max-studies 1000

clean:
	rm -rf data/*.duckdb
	rm -rf .pytest_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

docker:
	docker-compose up --build

docker-ingest:
	docker-compose run --rm pipeline ingest --max-studies 100

app:
	uv run streamlit run app.py
