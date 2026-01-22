"""Airflow DAG for Clinical Trial Pipeline orchestration.

This DAG orchestrates the existing pipeline steps without duplicating logic:
1. Ingest: Fetch studies from ClinicalTrials.gov API into raw layer
2. Staging: Apply SQL views to create Silver layer
3. Analytics: Validate Gold layer queries execute successfully
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# Project root (adjust if running from different location)
PROJECT_ROOT = "/app"

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="clinical_trial_pipeline",
    default_args=default_args,
    description="ELT pipeline for clinical trial data",
    schedule_interval=None,  # Manual trigger (set to "@daily" for scheduled runs)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["clinical-trials", "elt"],
) as dag:

    # Task 1: Ingest raw data from API
    ingest = BashOperator(
        task_id="ingest_raw_studies",
        bash_command=f"cd {PROJECT_ROOT} && python -m clinical_trial_pipeline.cli ingest --max-studies 100",
        doc="Fetch studies from ClinicalTrials.gov API and load into raw_studies table",
    )

    # Task 2: Apply staging views
    # Views are idempotent (CREATE OR REPLACE), safe to run repeatedly
    apply_staging = BashOperator(
        task_id="apply_staging_views",
        bash_command=f"""
cd {PROJECT_ROOT} && python -c "
import duckdb
from pathlib import Path

conn = duckdb.connect('data/clinical_trials.duckdb')
for sql_file in sorted(Path('sql/staging').glob('*.sql')):
    print(f'Applying {{sql_file.name}}')
    conn.execute(sql_file.read_text())
conn.close()
print('Staging views applied successfully')
"
""",
        doc="Apply staging SQL views (stg_studies, stg_conditions, etc.)",
    )

    # Task 3: Validate analytics queries
    # Run each query to ensure Gold layer is queryable
    validate_analytics = BashOperator(
        task_id="validate_analytics",
        bash_command=f"""
cd {PROJECT_ROOT} && python -c "
import duckdb
from pathlib import Path

conn = duckdb.connect('data/clinical_trials.duckdb')

# First apply staging views (required for analytics)
for sql_file in sorted(Path('sql/staging').glob('*.sql')):
    conn.execute(sql_file.read_text())

# Validate each analytics query
analytics_dir = Path('sql/analytics')
for sql_file in sorted(analytics_dir.glob('*.sql')):
    query = sql_file.read_text()
    result = conn.execute(query).fetchdf()
    row_count = len(result)
    print(f'{{sql_file.name}}: {{row_count}} rows')
    if row_count == 0:
        print(f'  WARNING: No data returned')

conn.close()
print('Analytics validation completed')
"
""",
        doc="Execute analytics queries to validate Gold layer",
    )

    # Define task dependencies
    ingest >> apply_staging >> validate_analytics
