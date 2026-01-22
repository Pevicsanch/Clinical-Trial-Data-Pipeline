# Airflow Orchestration

Minimal Airflow setup to orchestrate the clinical trial pipeline.

## DAG Overview

The `clinical_trial_pipeline` DAG executes three tasks:

```
ingest_raw_studies → apply_staging_views → validate_analytics
```

| Task | Description |
|------|-------------|
| `ingest_raw_studies` | Fetch studies from API into `raw_studies` |
| `apply_staging_views` | Apply SQL views from `sql/staging/` |
| `validate_analytics` | Run Gold layer queries and report row counts |

## Quick Start (Standalone Airflow)

```bash
# Install Airflow (in a separate venv recommended)
pip install apache-airflow

# Set Airflow home to this directory
export AIRFLOW_HOME=$(pwd)/airflow

# Initialize database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Start scheduler (terminal 1)
airflow scheduler

# Start webserver (terminal 2)
airflow webserver --port 8080
```

Access UI at http://localhost:8080

## Docker Compose Setup

For isolated Airflow execution, use the dedicated compose file:

```bash
docker-compose -f docker-compose.airflow.yml up -d
```

## Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| Executor | LocalExecutor | Single-node, sufficient for this pipeline |
| Schedule | Manual (`None`) | Trigger via UI or CLI |
| Retries | 1 | With 5-minute delay |

To enable daily scheduling, edit the DAG:
```python
schedule_interval="@daily"
```

## Manual Trigger

```bash
# Via CLI
airflow dags trigger clinical_trial_pipeline

# Or use the Airflow UI "Play" button
```

## Scheduling Readiness

### Why Manual by Default

The DAG uses `schedule_interval=None` (manual trigger) because:
- Appropriate scheduling frequency depends on data freshness requirements
- Avoids unnecessary API calls during development and testing
- Allows explicit control over when data is refreshed

### Enabling Scheduled Execution

To enable periodic runs, modify the DAG's `schedule_interval`:

```python
# Daily at midnight
schedule_interval="@daily"

# Every 6 hours
schedule_interval="0 */6 * * *"

# Hourly
schedule_interval="@hourly"
```

Choose frequency based on:
- How often ClinicalTrials.gov data is updated
- Acceptable data staleness for your use case
- API rate limits and courtesy considerations

### Idempotent Ingestion

The pipeline is safe for repeated execution:

```
# First run
Inserted: 50, Skipped: 0

# Second run (same data)
Inserted: 0, Skipped: 50
```

This behavior is guaranteed by:
- **Content hash deduplication**: Each study's JSON is hashed; duplicates are skipped via unique constraint
- **Append-only raw layer**: No updates or deletes; new versions of studies create new records
- **Idempotent views**: Staging uses `CREATE OR REPLACE VIEW`

This makes periodic scheduling safe—running the DAG multiple times will not corrupt or duplicate data.

## Notes

- The DAG reuses existing CLI and SQL files (no logic duplication)
- Staging views are idempotent (`CREATE OR REPLACE VIEW`)
- Analytics validation logs row counts for monitoring
- This setup is independent of the main `docker-compose.yml`
