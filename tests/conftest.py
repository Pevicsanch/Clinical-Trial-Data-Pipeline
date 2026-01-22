"""Pytest configuration for test suite."""

import os

# Configure Airflow environment before any imports
os.environ.setdefault("AIRFLOW_HOME", "/tmp/airflow_test")
os.environ.setdefault("AIRFLOW__CORE__UNIT_TEST_MODE", "True")
os.environ.setdefault("AIRFLOW__CORE__LOAD_EXAMPLES", "False")
