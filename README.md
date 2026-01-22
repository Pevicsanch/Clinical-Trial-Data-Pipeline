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

Staging models are defined as SQL views and applied at runtime before executing analytics queries.

### Data Source

- [ClinicalTrials.gov API v2](https://clinicaltrials.gov/api/v2/studies)

## Pipeline Steps

1. Ingest raw studies from the API into DuckDB (`raw_studies`)
2. Apply staging views (`stg_*`) from `sql/staging/`
3. Run analytics queries from `sql/analytics/` (Gold)
4. Optional: explore results with Streamlit (reads Gold queries)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| Package Manager | [uv](https://github.com/astral-sh/uv) |
| Database | DuckDB |
| HTTP Client | requests |
| Testing | pytest |
| Containerization | Docker |
| Dashboard | Streamlit |

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

### Makefile

```bash
make install      # Install dependencies
make test         # Run tests
make ingest       # Ingest 100 studies
make ingest-full  # Ingest 1000 studies
make app          # Run Streamlit dashboard
make docker-build # Build Docker image
make docker-run   # Run ingestion in Docker
make clean        # Remove generated files
```

### Orchestration (Optional)

Airflow DAG for scheduling and orchestration:

```bash
# Using Docker
docker-compose -f docker-compose.airflow.yml up -d

# Access Airflow UI at http://localhost:8080 (admin/admin)
```

See [airflow/README.md](airflow/README.md) for details.

### Scheduling

By default, the pipeline runs on manual trigger (CLI or Airflow UI) to avoid unnecessary API calls during development and evaluation.

Periodic execution can be enabled via Airflow by configuring the DAG schedule (e.g. `@daily`, `@hourly`, or cron expressions).
The ingestion process is idempotent, so repeated scheduled runs are safe and do not create duplicate records.

### Dashboard

```bash
# Start Streamlit app (requires data to be ingested first)
make ingest
make app
```

Opens at http://localhost:8501 with:
- Total studies, conditions, countries metrics
- Trials by phase chart
- Top conditions chart
- Geographic distribution
- Completion rates by intervention type

The dashboard is intentionally lightweight and serves as a visual validation of the analytics (Gold) layer, not as a full BI solution.

### Dashboard (Docker)

The Docker image is intentionally focused on the data pipeline.

The Streamlit dashboard is provided as a lightweight validation and exploration UI.
When needed, it can be executed in Docker via volume mounting, without coupling
the UI to the core pipeline image.

Example:

```bash
docker run --rm -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/app.py:/app/app.py \
  --entrypoint uv clinical-pipeline \
  run streamlit run app.py --server.address 0.0.0.0 --server.headless true
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

*Completion rate is defined as the percentage of studies with `overall_status = 'COMPLETED'` per intervention type.*

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
- Enables safe repeated execution (idempotent ingestion for scheduled runs)

### Why SQL views for staging?

- Demonstrates SQL proficiency
- No data duplication (views read from raw)
- Schema changes don't require re-ingestion

### Why `requests` over `httpx`?

- ClinicalTrials.gov blocks `httpx` User-Agent
- `requests` works out of the box with no configuration

## Limitations

- Live API data may vary between runs (no snapshot guarantees)
- Some fields contain missing or inconsistent values (handled as nulls)
- Gold layer uses on-demand queries, not materialized tables
- Dashboard serves as validation UI, not a production BI tool

## Production Considerations

### Scalability

To handle 100x more data volume:

- **Partitioning**: Partition raw tables by ingestion date for faster queries
- **Incremental ingestion**: Use API-side filters based on update timestamps (when available) to fetch only new/updated studies
- **Parallel processing**: Batch API requests with async/multiprocessing
- **Storage**: Export to Parquet files partitioned by year/month for analytical workloads
- **Infrastructure**: Move from embedded DuckDB to MotherDuck or a distributed query engine

### Data Quality

Additional validation rules for clinical trial data:

- **Schema validation**: Enforce required fields (nct_id, study_type, status)
- **Referential integrity**: Validate foreign keys between staging tables
- **Business rules**: Flag studies with enrollment > 100,000 as potential data errors
- **Date consistency**: Ensure start_date < completion_date
- **Enum validation**: Validate phase, status against known values
- **Duplicates**: Alert on studies with same title but different NCT IDs

### Compliance (GxP)

For a GxP-regulated environment:

- **Audit trails**: Log all data modifications with timestamps and user IDs
- **Data integrity**: Implement ALCOA+ principles (Attributable, Legible, Contemporaneous, Original, Accurate)
- **Validation**: IQ/OQ/PQ documentation for the pipeline
- **Change control**: Version control for all SQL transformations with approval workflows
- **Access control**: Role-based access to raw vs. transformed data
- **Retention**: Define data retention policies aligned with regulatory requirements

### Monitoring

Production monitoring strategy:

- **Pipeline metrics**: Track ingestion rate, success/failure counts, latency
- **Data quality metrics**: Monitor null rates, schema drift, row counts per run
- **Alerts**: Notify on API errors, ingestion failures, unexpected data patterns
- **Logging**: Centralized logging with correlation IDs for traceability
- **Dashboards**: Grafana/Datadog for real-time pipeline health visibility

### Security

Security measures for sensitive clinical data:

- **Encryption**: Encrypt data at rest (DuckDB encryption) and in transit (TLS)
- **Access control**: Implement least-privilege access to database and API credentials
- **Secrets management**: Use environment variables or vault for API keys
- **Network**: Restrict outbound traffic to known API endpoints
- **Anonymization**: Remove or hash PII if processing patient-level data
- **Audit logging**: Log all data access for security review
