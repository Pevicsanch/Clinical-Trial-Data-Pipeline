"""Tests for ingestion service."""

import pytest

from clinical_trial_pipeline.load.ingestion import IngestResult, IngestService
from clinical_trial_pipeline.extract.clinicaltrials_client import ClinicalTrialsAPIError


class TestIngestResult:
    """Tests for IngestResult dataclass."""

    def test_total_processed(self):
        result = IngestResult(inserted=10, skipped=5)
        assert result.total_processed == 15

    def test_str_representation(self):
        result = IngestResult(inserted=10, skipped=5, pages=2)
        assert "inserted=10" in str(result)
        assert "skipped=5" in str(result)
        assert "pages=2" in str(result)

    def test_errors_default_empty(self):
        result = IngestResult()
        assert result.errors == []


class TestIngestService:
    """Tests for IngestService."""

    def test_run_single_page(self, mocker):
        # Mock database
        mock_db = mocker.MagicMock()
        mock_db.__enter__ = mocker.Mock(return_value=mock_db)
        mock_db.__exit__ = mocker.Mock(return_value=False)
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.Database",
            return_value=mock_db,
        )

        # Mock repository
        mock_repo = mocker.MagicMock()
        mock_repo.insert_studies_batch.return_value = (3, 0)
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.RawStudyRepository",
            return_value=mock_repo,
        )

        # Mock API client
        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)
        mock_client.fetch_studies.return_value = {
            "studies": [
                {"protocolSection": {"identificationModule": {"nctId": "NCT001"}}},
                {"protocolSection": {"identificationModule": {"nctId": "NCT002"}}},
                {"protocolSection": {"identificationModule": {"nctId": "NCT003"}}},
            ],
            "nextPageToken": None,
        }
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.ClinicalTrialsClient",
            return_value=mock_client,
        )

        service = IngestService(db_path=":memory:")
        result = service.run()

        assert result.inserted == 3
        assert result.skipped == 0
        assert result.pages == 1
        assert result.errors == []

    def test_run_multiple_pages(self, mocker):
        mock_db = mocker.MagicMock()
        mock_db.__enter__ = mocker.Mock(return_value=mock_db)
        mock_db.__exit__ = mocker.Mock(return_value=False)
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.Database",
            return_value=mock_db,
        )

        mock_repo = mocker.MagicMock()
        mock_repo.insert_studies_batch.return_value = (2, 0)
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.RawStudyRepository",
            return_value=mock_repo,
        )

        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)
        mock_client.fetch_studies.side_effect = [
            {"studies": [{"nctId": "NCT001"}, {"nctId": "NCT002"}], "nextPageToken": "token1"},
            {"studies": [{"nctId": "NCT003"}, {"nctId": "NCT004"}], "nextPageToken": "token2"},
            {"studies": [{"nctId": "NCT005"}], "nextPageToken": None},
        ]
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.ClinicalTrialsClient",
            return_value=mock_client,
        )

        service = IngestService(db_path=":memory:")
        result = service.run()

        assert result.pages == 3
        assert result.inserted == 6  # 2 + 2 + 2 (mocked)

    def test_run_respects_max_pages(self, mocker):
        mock_db = mocker.MagicMock()
        mock_db.__enter__ = mocker.Mock(return_value=mock_db)
        mock_db.__exit__ = mocker.Mock(return_value=False)
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.Database",
            return_value=mock_db,
        )

        mock_repo = mocker.MagicMock()
        mock_repo.insert_studies_batch.return_value = (2, 0)
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.RawStudyRepository",
            return_value=mock_repo,
        )

        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)
        mock_client.fetch_studies.return_value = {
            "studies": [{"nctId": "NCT001"}, {"nctId": "NCT002"}],
            "nextPageToken": "token",
        }
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.ClinicalTrialsClient",
            return_value=mock_client,
        )

        service = IngestService(db_path=":memory:")
        result = service.run(max_pages=2)

        assert result.pages == 2
        assert mock_client.fetch_studies.call_count == 2

    def test_run_respects_max_studies(self, mocker):
        mock_db = mocker.MagicMock()
        mock_db.__enter__ = mocker.Mock(return_value=mock_db)
        mock_db.__exit__ = mocker.Mock(return_value=False)
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.Database",
            return_value=mock_db,
        )

        mock_repo = mocker.MagicMock()
        mock_repo.insert_studies_batch.return_value = (5, 0)
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.RawStudyRepository",
            return_value=mock_repo,
        )

        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)
        mock_client.fetch_studies.return_value = {
            "studies": [{"nctId": f"NCT{i}"} for i in range(5)],
            "nextPageToken": "token",
        }
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.ClinicalTrialsClient",
            return_value=mock_client,
        )

        service = IngestService(db_path=":memory:", page_size=5)
        result = service.run(max_studies=5)

        assert result.total_processed == 5
        assert result.pages == 1

    def test_run_handles_api_error(self, mocker):
        mock_db = mocker.MagicMock()
        mock_db.__enter__ = mocker.Mock(return_value=mock_db)
        mock_db.__exit__ = mocker.Mock(return_value=False)
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.Database",
            return_value=mock_db,
        )

        mock_repo = mocker.MagicMock()
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.RawStudyRepository",
            return_value=mock_repo,
        )

        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)
        mock_client.fetch_studies.side_effect = ClinicalTrialsAPIError("Connection failed")
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.ClinicalTrialsClient",
            return_value=mock_client,
        )

        service = IngestService(db_path=":memory:")
        result = service.run()

        assert result.pages == 0
        assert len(result.errors) == 1
        assert "Connection failed" in result.errors[0]

    def test_run_handles_empty_response(self, mocker):
        mock_db = mocker.MagicMock()
        mock_db.__enter__ = mocker.Mock(return_value=mock_db)
        mock_db.__exit__ = mocker.Mock(return_value=False)
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.Database",
            return_value=mock_db,
        )

        mock_repo = mocker.MagicMock()
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.RawStudyRepository",
            return_value=mock_repo,
        )

        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)
        mock_client.fetch_studies.return_value = {"studies": [], "nextPageToken": None}
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.ClinicalTrialsClient",
            return_value=mock_client,
        )

        service = IngestService(db_path=":memory:")
        result = service.run()

        assert result.pages == 0
        assert result.inserted == 0

    def test_run_with_skipped_duplicates(self, mocker):
        mock_db = mocker.MagicMock()
        mock_db.__enter__ = mocker.Mock(return_value=mock_db)
        mock_db.__exit__ = mocker.Mock(return_value=False)
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.Database",
            return_value=mock_db,
        )

        mock_repo = mocker.MagicMock()
        mock_repo.insert_studies_batch.return_value = (2, 3)  # 2 inserted, 3 skipped
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.RawStudyRepository",
            return_value=mock_repo,
        )

        mock_client = mocker.MagicMock()
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)
        mock_client.fetch_studies.return_value = {
            "studies": [{"nctId": f"NCT{i}"} for i in range(5)],
            "nextPageToken": None,
        }
        mocker.patch(
            "clinical_trial_pipeline.load.ingestion.ClinicalTrialsClient",
            return_value=mock_client,
        )

        service = IngestService(db_path=":memory:")
        result = service.run()

        assert result.inserted == 2
        assert result.skipped == 3
        assert result.total_processed == 5
