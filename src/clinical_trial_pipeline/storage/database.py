"""DuckDB database connection management."""

from pathlib import Path

import duckdb

from clinical_trial_pipeline.common.logging import get_logger

logger = get_logger(__name__)

DEFAULT_DB_PATH = Path("data/clinical_trials.duckdb")


class Database:
    """DuckDB database connection manager."""

    def __init__(self, db_path: Path | str | None = None):
        """Initialize database connection.

        Args:
            db_path: Path to DuckDB file. If None, uses default path.
                     Use ":memory:" for in-memory database.
        """
        if db_path is None:
            db_path = DEFAULT_DB_PATH

        self.db_path = Path(db_path) if db_path != ":memory:" else db_path
        self._connection: duckdb.DuckDBPyConnection | None = None

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Establish database connection."""
        if self._connection is not None:
            return self._connection

        if self.db_path != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = duckdb.connect(str(self.db_path))
        logger.info("Connected to database: %s", self.db_path)
        return self._connection

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Get active connection, creating one if needed."""
        if self._connection is None:
            return self.connect()
        return self._connection

    def close(self) -> None:
        """Close database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()
