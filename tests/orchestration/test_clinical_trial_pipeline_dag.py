"""Tests for Clinical Trial Pipeline Airflow DAG.

Validates DAG structure and task dependencies without executing Airflow.
"""

from pathlib import Path

import pytest
from airflow.models import DagBag
from airflow.operators.bash import BashOperator


DAGS_FOLDER = Path(__file__).parent.parent.parent / "orchestration" / "dags"
DAG_ID = "clinical_trial_pipeline"

EXPECTED_TASKS = [
    "ingest_raw_studies",
    "apply_staging_views",
    "validate_analytics",
]


@pytest.fixture(scope="module")
def dagbag():
    """Load DAGs from the airflow/dags folder."""
    return DagBag(dag_folder=str(DAGS_FOLDER), include_examples=False)


@pytest.fixture(scope="module")
def dag(dagbag):
    """Get the clinical trial pipeline DAG."""
    return dagbag.dags.get(DAG_ID)


class TestDAGImport:
    """Test DAG can be imported without errors."""

    def test_dagbag_has_no_import_errors(self, dagbag):
        """DAG files should import without syntax or import errors."""
        assert dagbag.import_errors == {}, f"DAG import errors: {dagbag.import_errors}"

    def test_dag_exists(self, dagbag):
        """The clinical_trial_pipeline DAG should exist."""
        assert DAG_ID in dagbag.dags, f"DAG '{DAG_ID}' not found in {list(dagbag.dags.keys())}"


class TestDAGStructure:
    """Test DAG structure and configuration."""

    def test_dag_id(self, dag):
        """DAG should have the expected ID."""
        assert dag.dag_id == DAG_ID

    def test_dag_has_expected_tasks(self, dag):
        """DAG should contain exactly the expected tasks."""
        task_ids = [task.task_id for task in dag.tasks]
        assert sorted(task_ids) == sorted(EXPECTED_TASKS), (
            f"Expected tasks {EXPECTED_TASKS}, got {task_ids}"
        )

    def test_dag_task_count(self, dag):
        """DAG should have exactly 3 tasks."""
        assert len(dag.tasks) == 3


class TestTaskDependencies:
    """Test task dependency chain."""

    def test_ingest_has_no_upstream(self, dag):
        """ingest_raw_studies should have no upstream dependencies."""
        task = dag.get_task("ingest_raw_studies")
        assert len(task.upstream_task_ids) == 0

    def test_apply_staging_depends_on_ingest(self, dag):
        """apply_staging_views should depend on ingest_raw_studies."""
        task = dag.get_task("apply_staging_views")
        assert "ingest_raw_studies" in task.upstream_task_ids

    def test_validate_analytics_depends_on_staging(self, dag):
        """validate_analytics should depend on apply_staging_views."""
        task = dag.get_task("validate_analytics")
        assert "apply_staging_views" in task.upstream_task_ids

    def test_validate_analytics_is_terminal(self, dag):
        """validate_analytics should have no downstream dependencies."""
        task = dag.get_task("validate_analytics")
        assert len(task.downstream_task_ids) == 0

    def test_full_dependency_chain(self, dag):
        """Dependency chain should be: ingest >> staging >> analytics."""
        ingest = dag.get_task("ingest_raw_studies")
        staging = dag.get_task("apply_staging_views")
        analytics = dag.get_task("validate_analytics")

        # Verify linear chain
        assert ingest.downstream_task_ids == {"apply_staging_views"}
        assert staging.upstream_task_ids == {"ingest_raw_studies"}
        assert staging.downstream_task_ids == {"validate_analytics"}
        assert analytics.upstream_task_ids == {"apply_staging_views"}


class TestTaskOperators:
    """Test tasks use the expected operators."""

    def test_all_tasks_use_bash_operator(self, dag):
        """All tasks should use BashOperator."""
        for task in dag.tasks:
            assert isinstance(task, BashOperator), (
                f"Task '{task.task_id}' should use BashOperator, got {type(task).__name__}"
            )

    def test_ingest_uses_cli_command(self, dag):
        """ingest task should call the pipeline CLI."""
        task = dag.get_task("ingest_raw_studies")
        assert "clinical_trial_pipeline.cli" in task.bash_command
        assert "ingest" in task.bash_command

    def test_staging_applies_sql_files(self, dag):
        """staging task should reference sql/staging directory."""
        task = dag.get_task("apply_staging_views")
        assert "sql/staging" in task.bash_command

    def test_analytics_validates_queries(self, dag):
        """analytics task should reference sql/analytics directory."""
        task = dag.get_task("validate_analytics")
        assert "sql/analytics" in task.bash_command
