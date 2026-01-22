"""Repository for raw studies storage."""

import hashlib
import json
from pathlib import Path
from typing import Any

import duckdb

from clinical_trial_pipeline.common.logging import get_logger
from clinical_trial_pipeline.storage.database import Database

logger = get_logger(__name__)

DDL_PATH = Path(__file__).parent.parent.parent.parent / "sql" / "raw" / "001_create_raw_studies.sql"
DEFAULT_SOURCE = "clinicaltrials_api_v2"


def compute_content_hash(data: dict[str, Any]) -> str:
    """Compute SHA-256 hash of JSON content."""
    content = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content.encode()).hexdigest()


class RawStudyRepository:
    """Repository for raw study data (bronze layer)."""

    def __init__(self, database: Database):
        self.db = database
        self._initialized = False

    def initialize(self) -> None:
        """Create tables if they don't exist."""
        if self._initialized:
            return

        ddl = DDL_PATH.read_text()
        self.db.connection.execute(ddl)
        self._initialized = True
        logger.info("Raw studies table initialized")

    def insert_study(
        self,
        nct_id: str,
        raw_json: dict[str, Any],
        source: str = DEFAULT_SOURCE,
    ) -> bool:
        """Insert a raw study record.

        Args:
            nct_id: Clinical trial identifier
            raw_json: Raw JSON payload from API
            source: Data source identifier

        Returns:
            True if inserted, False if duplicate (same content_hash)
        """
        content_hash = compute_content_hash(raw_json)

        try:
            self.db.connection.execute(
                """
                INSERT INTO raw_studies (nct_id, source, raw_json, content_hash)
                VALUES (?, ?, ?, ?)
                """,
                [nct_id, source, json.dumps(raw_json), content_hash],
            )
            logger.debug("Inserted study %s", nct_id)
            return True
        except duckdb.ConstraintException:
            logger.debug("Skipped duplicate study %s (hash: %s...)", nct_id, content_hash[:8])
            return False

    def insert_studies_batch(
        self,
        studies: list[dict[str, Any]],
        source: str = DEFAULT_SOURCE,
    ) -> tuple[int, int]:
        """Insert multiple studies.

        Args:
            studies: List of raw study payloads
            source: Data source identifier

        Returns:
            Tuple of (inserted_count, skipped_count)
        """
        inserted = 0
        skipped = 0

        for study in studies:
            nct_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
            if nct_id is None:
                logger.warning("Study missing nctId, skipping")
                skipped += 1
                continue

            if self.insert_study(nct_id, study, source):
                inserted += 1
            else:
                skipped += 1

        logger.info("Batch insert complete: %d inserted, %d skipped", inserted, skipped)
        return inserted, skipped

    def get_study_by_nct_id(self, nct_id: str) -> list[dict[str, Any]]:
        """Get all versions of a study by NCT ID.

        Returns:
            List of study records (may have multiple versions)
        """
        result = self.db.connection.execute(
            """
            SELECT id, nct_id, source, raw_json, content_hash, ingested_at
            FROM raw_studies
            WHERE nct_id = ?
            ORDER BY ingested_at DESC
            """,
            [nct_id],
        ).fetchall()

        return [
            {
                "id": row[0],
                "nct_id": row[1],
                "source": row[2],
                "raw_json": json.loads(row[3]),
                "content_hash": row[4],
                "ingested_at": row[5],
            }
            for row in result
        ]

    def get_latest_study(self, nct_id: str) -> dict[str, Any] | None:
        """Get the most recent version of a study."""
        studies = self.get_study_by_nct_id(nct_id)
        return studies[0] if studies else None

    def count_studies(self) -> int:
        """Count total raw study records."""
        result = self.db.connection.execute("SELECT COUNT(*) FROM raw_studies").fetchone()
        return result[0] if result else 0

    def count_unique_studies(self) -> int:
        """Count unique NCT IDs."""
        result = self.db.connection.execute(
            "SELECT COUNT(DISTINCT nct_id) FROM raw_studies"
        ).fetchone()
        return result[0] if result else 0
