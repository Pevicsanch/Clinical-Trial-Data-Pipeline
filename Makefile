.PHONY: install test lint ingest ingest-full clean docker docker-ingest docker-app app inspect-db inspect-raw

# Sentinel file to track installation state
.venv/.installed: pyproject.toml uv.lock
	uv sync
	uv pip install -e .
	@touch .venv/.installed

install: .venv/.installed

test: .venv/.installed
	uv run pytest tests/ -v

lint: .venv/.installed
	uv run ruff check src/ tests/

ingest: .venv/.installed
	uv run python -m clinical_trial_pipeline.cli ingest --max-studies 100

ingest-full: .venv/.installed
	uv run python -m clinical_trial_pipeline.cli ingest --max-studies 1000

app: .venv/.installed
	uv run streamlit run app.py

inspect-db: .venv/.installed
	uv run python -c "import duckdb; [print(t[0]) for t in duckdb.connect('data/clinical_trials.duckdb').execute('SHOW TABLES').fetchall()]"

inspect-raw: .venv/.installed
	uv run python -c "import duckdb; print('raw_studies:', duckdb.connect('data/clinical_trials.duckdb').execute('SELECT COUNT(*) FROM raw_studies').fetchone()[0], 'rows')"

clean:
	rm -rf data/*.duckdb
	rm -rf .pytest_cache
	rm -rf .venv/.installed
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

docker:
	docker-compose up --build

docker-ingest:
	docker-compose run --rm pipeline ingest --max-studies 100

docker-app:
	docker run --rm -p 8501:8501 -v $(PWD)/data:/app/data -v $(PWD)/app.py:/app/app.py --entrypoint uv clinical-pipeline run streamlit run app.py --server.address 0.0.0.0 --server.headless true
