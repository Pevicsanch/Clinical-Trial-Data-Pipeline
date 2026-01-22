# Clinical Trial Data Pipeline

ELT data pipeline that ingests clinical trial data from ClinicalTrials.gov API, transforming it into analytics-ready datasets.

## Overview

This project implements a production-inspired data pipeline for processing clinical trial data. It follows modern data engineering practices with a focus on:

- **Reproducibility** — Deterministic runs with locked dependencies
- **Data Quality** — Validation and deduplication at ingestion
- **Traceability** — Raw data preservation with full lineage

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Extract       │     │     Load        │     │   Transform     │
│                 │     │                 │     │                 │
│ ClinicalTrials  │────▶│  Raw (Bronze)   │────▶│ Staging/Analytics│
│ .gov API v2     │     │  DuckDB         │     │ (Silver/Gold)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Data Layers

| Layer | Purpose | Implementation |
|-------|---------|----------------|
| **Raw (Bronze)** | Preserve original API responses | `raw_studies` table |
| **Staging (Silver)** | Normalized, typed data | `stg_studies`, `stg_conditions`, `stg_interventions`, `stg_locations` |
| **Analytics (Gold)** | Aggregated metrics | SQL queries for trials, conditions, interventions, geography |

### Data Source

- [ClinicalTrials.gov API v2](https://clinicaltrials.gov/api/v2/studies)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| Package Manager | [uv](https://github.com/astral-sh/uv) |
| Database | DuckDB |
| HTTP Client | requests |
| Testing | pytest |
| Containerization | Docker |

## Project Structure

```
├── src/clinical_trial_pipeline/
│   ├── cli.py             # CLI entrypoint
│   ├── extract/           # API clients
│   ├── load/              # Ingestion service
│   ├── storage/           # Database & repositories
│   └── common/            # Logging, utilities
├── sql/
│   ├── raw/               # Bronze layer DDL
│   ├── staging/           # Silver layer views
│   └── analytics/         # Gold layer queries
└── tests/
```

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

### Installation

```bash
git clone <repository-url>
cd Clinical-Trial-Data-Pipeline
uv sync
uv pip install -e .
```

### Ingest Data

```bash
# Ingest 500 studies from the API
uv run python -m clinical_trial_pipeline.cli ingest --max-studies 500

# Custom database path
uv run python -m clinical_trial_pipeline.cli ingest --db-path data/trials.duckdb --max-studies 1000
```

### Run Tests

```bash
uv run pytest tests/ -v
```

### Docker

```bash
# Build image
docker build -t clinical-pipeline .

# Run ingestion
docker run --rm -v $(pwd)/data:/app/data clinical-pipeline ingest --max-studies 500

# Or use docker-compose
docker-compose up
```

## Data Models

### Staging Layer (Silver)

| Model | Description |
|-------|-------------|
| `stg_studies` | Core study attributes (type, phase, status, enrollment, dates, sponsor) |
| `stg_conditions` | Conditions being studied (1:N with studies) |
| `stg_interventions` | Interventions used (1:N with studies) |
| `stg_locations` | Study locations with coordinates (1:N with studies) |

### Analytics Queries (Gold)

| Query | Question Answered |
|-------|-------------------|
| `trials_by_phase.sql` | How many trials by study type and phase? |
| `top_conditions.sql` | What are the most common conditions? |
| `interventions_completion_rate.sql` | Which interventions have highest completion rates? |
| `trials_by_country.sql` | Geographic distribution of trials? |
| `study_duration.sql` | Average study duration by type and phase? |

### Example: Run Analytics

```python
from clinical_trial_pipeline.storage.database import Database
from pathlib import Path

with Database("data/clinical_trials.duckdb") as db:
    # Apply staging views
    for sql_file in sorted(Path("sql/staging").glob("*.sql")):
        db.connection.execute(sql_file.read_text())

    # Run analytics query
    query = Path("sql/analytics/trials_by_phase.sql").read_text()
    results = db.connection.execute(query).fetchall()
```

## Design Decisions

### Why DuckDB?

- Zero setup (embedded, like SQLite)
- Columnar storage optimized for analytics
- Native JSON support for parsing raw API responses
- Easy export to Parquet for downstream tools

### Why append-only raw layer?

- Preserves data history for auditing
- Allows reprocessing with different transformation logic
- Deduplication via content hash prevents redundant storage

### Why SQL views for staging?

- Demonstrates SQL proficiency
- No data duplication (views read from raw)
- Schema changes don't require re-ingestion

### Why `requests` over `httpx`?

- ClinicalTrials.gov blocks `httpx` User-Agent
- `requests` works out of the box with no configuration
