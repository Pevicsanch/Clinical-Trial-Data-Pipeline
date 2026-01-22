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

## Notes

- The DAG reuses existing CLI and SQL files (no logic duplication)
- Staging views are idempotent (`CREATE OR REPLACE VIEW`)
- Analytics validation logs row counts for monitoring
- This setup is independent of the main `docker-compose.yml`
