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

| Layer | Purpose | Storage |
|-------|---------|---------|
| **Raw** | Preserve original API responses (append-only) | `raw_studies` table |
| **Staging** | Cleaned and normalized data | *Coming soon* |
| **Analytics** | Aggregated metrics and dimensional models | *Coming soon* |

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

## Project Structure

```
├── src/clinical_trial_pipeline/
│   ├── extract/        # API clients
│   ├── load/           # Data loading logic
│   ├── transform/      # Data transformations
│   ├── storage/        # Database connections & repositories
│   ├── common/         # Logging, config, utilities
│   └── domain/         # Domain entities
├── sql/
│   ├── raw/            # Bronze layer DDL
│   ├── staging/        # Silver layer transformations
│   └── analytics/      # Analytical queries
└── tests/
```

## Setup

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

### Running Tests

```bash
uv run pytest tests/ -v
```

## Usage

### Fetch studies from API

```python
from clinical_trial_pipeline.extract.clinicaltrials_client import ClinicalTrialsClient

with ClinicalTrialsClient() as client:
    data = client.fetch_studies(page_size=100)
    studies = data["studies"]
    next_token = data.get("nextPageToken")
```

### Store raw data

```python
from clinical_trial_pipeline.storage.database import Database
from clinical_trial_pipeline.storage.raw_repository import RawStudyRepository

with Database("data/clinical_trials.duckdb") as db:
    repo = RawStudyRepository(db)
    repo.initialize()

    inserted, skipped = repo.insert_studies_batch(studies)
```

## Design Decisions

### Why DuckDB?

- Zero setup (embedded, like SQLite)
- Columnar storage optimized for analytics
- Native JSON support
- Easy export to Parquet for downstream tools

### Why append-only raw layer?

- Preserves data history for auditing
- Allows reprocessing with different transformation logic
- Deduplication via content hash prevents redundant storage

### Why `requests` over `httpx`?

- ClinicalTrials.gov blocks `httpx` User-Agent
- `requests` works out of the box with no configuration
