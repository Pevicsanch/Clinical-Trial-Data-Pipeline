"""Ingestion service for loading raw clinical trial data."""

from dataclasses import dataclass, field
from pathlib import Path

from clinical_trial_pipeline.common.logging import get_logger
from clinical_trial_pipeline.extract.clinicaltrials_client import (
    ClinicalTrialsClient,
    ClinicalTrialsAPIError,
)
from clinical_trial_pipeline.storage.database import Database
from clinical_trial_pipeline.storage.raw_repository import RawStudyRepository

logger = get_logger(__name__)


@dataclass
class IngestResult:
    """Result of an ingestion run."""

    inserted: int = 0
    skipped: int = 0
    pages: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return self.inserted + self.skipped

    def __str__(self) -> str:
        return (
            f"IngestResult(inserted={self.inserted}, skipped={self.skipped}, "
            f"pages={self.pages}, errors={len(self.errors)})"
        )


class IngestService:
    """Service for ingesting clinical trial data from API to raw storage."""

    def __init__(
        self,
        db_path: Path | str = "data/clinical_trials.duckdb",
        page_size: int = 100,
    ):
        """Initialize ingestion service.

        Args:
            db_path: Path to DuckDB database file
            page_size: Number of studies per API request
        """
        self.db_path = db_path
        self.page_size = page_size

    def run(
        self,
        max_studies: int | None = None,
        max_pages: int | None = None,
    ) -> IngestResult:
        """Run ingestion process.

        Args:
            max_studies: Maximum number of studies to ingest (None for unlimited)
            max_pages: Maximum number of API pages to fetch (None for unlimited)

        Returns:
            IngestResult with counts and any errors
        """
        result = IngestResult()

        with Database(self.db_path) as db:
            repo = RawStudyRepository(db)
            repo.initialize()

            with ClinicalTrialsClient() as client:
                page_token = None

                while True:
                    # Check page limit
                    if max_pages is not None and result.pages >= max_pages:
                        logger.info("Reached max pages limit: %d", max_pages)
                        break

                    # Check study limit
                    if max_studies is not None and result.total_processed >= max_studies:
                        logger.info("Reached max studies limit: %d", max_studies)
                        break

                    # Calculate page size for this request
                    request_page_size = self.page_size
                    if max_studies is not None:
                        remaining = max_studies - result.total_processed
                        request_page_size = min(self.page_size, remaining)

                    # Fetch page
                    try:
                        data = client.fetch_studies(
                            page_token=page_token,
                            page_size=request_page_size,
                        )
                    except ClinicalTrialsAPIError as e:
                        error_msg = f"API error on page {result.pages + 1}: {e}"
                        logger.error(error_msg)
                        result.errors.append(error_msg)
                        break

                    studies = data.get("studies", [])
                    if not studies:
                        logger.info("No more studies to fetch")
                        break

                    # Insert into raw storage
                    inserted, skipped = repo.insert_studies_batch(studies)
                    result.inserted += inserted
                    result.skipped += skipped
                    result.pages += 1

                    logger.info(
                        "Page %d: inserted=%d, skipped=%d, total=%d",
                        result.pages,
                        inserted,
                        skipped,
                        result.total_processed,
                    )

                    # Check for next page
                    page_token = data.get("nextPageToken")
                    if not page_token:
                        logger.info("No more pages available")
                        break

        logger.info("Ingestion complete: %s", result)
        return result
