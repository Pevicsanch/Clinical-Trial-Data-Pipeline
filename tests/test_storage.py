"""Tests for storage layer."""

import pytest

from clinical_trial_pipeline.storage.database import Database
from clinical_trial_pipeline.storage.raw_repository import (
    RawStudyRepository,
    compute_content_hash,
)


class TestComputeContentHash:
    """Tests for content hash computation."""

    def test_same_content_same_hash(self):
        data1 = {"a": 1, "b": 2}
        data2 = {"a": 1, "b": 2}
        assert compute_content_hash(data1) == compute_content_hash(data2)

    def test_different_content_different_hash(self):
        data1 = {"a": 1}
        data2 = {"a": 2}
        assert compute_content_hash(data1) != compute_content_hash(data2)

    def test_key_order_does_not_matter(self):
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}
        assert compute_content_hash(data1) == compute_content_hash(data2)


class TestDatabase:
    """Tests for Database connection manager."""

    def test_connect_in_memory(self):
        db = Database(":memory:")
        conn = db.connect()
        assert conn is not None
        db.close()

    def test_context_manager(self):
        with Database(":memory:") as db:
            assert db.connection is not None

    def test_connection_property_creates_connection(self):
        db = Database(":memory:")
        assert db._connection is None
        _ = db.connection
        assert db._connection is not None
        db.close()


class TestRawStudyRepository:
    """Tests for RawStudyRepository."""

    @pytest.fixture
    def repo(self):
        """Create an initialized repository with in-memory database."""
        db = Database(":memory:")
        db.connect()
        repo = RawStudyRepository(db)
        repo.initialize()
        yield repo
        db.close()

    def test_initialize_creates_table(self, repo):
        result = repo.db.connection.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'raw_studies'"
        ).fetchone()
        assert result[0] == 1

    def test_insert_study_success(self, repo):
        raw_json = {"protocolSection": {"identificationModule": {"nctId": "NCT001"}}}
        result = repo.insert_study("NCT001", raw_json)
        assert result is True
        assert repo.count_studies() == 1

    def test_insert_study_duplicate_skipped(self, repo):
        raw_json = {"protocolSection": {"identificationModule": {"nctId": "NCT001"}}}
        repo.insert_study("NCT001", raw_json)
        result = repo.insert_study("NCT001", raw_json)
        assert result is False
        assert repo.count_studies() == 1

    def test_insert_same_nct_id_different_content(self, repo):
        raw_json1 = {"version": 1, "nctId": "NCT001"}
        raw_json2 = {"version": 2, "nctId": "NCT001"}

        repo.insert_study("NCT001", raw_json1)
        repo.insert_study("NCT001", raw_json2)

        assert repo.count_studies() == 2
        assert repo.count_unique_studies() == 1

    def test_insert_studies_batch(self, repo):
        studies = [
            {"protocolSection": {"identificationModule": {"nctId": "NCT001"}}},
            {"protocolSection": {"identificationModule": {"nctId": "NCT002"}}},
            {"protocolSection": {"identificationModule": {"nctId": "NCT003"}}},
        ]
        inserted, skipped = repo.insert_studies_batch(studies)
        assert inserted == 3
        assert skipped == 0

    def test_insert_studies_batch_skips_missing_nct_id(self, repo):
        studies = [
            {"protocolSection": {"identificationModule": {"nctId": "NCT001"}}},
            {"protocolSection": {"identificationModule": {}}},  # Missing nctId
        ]
        inserted, skipped = repo.insert_studies_batch(studies)
        assert inserted == 1
        assert skipped == 1

    def test_get_study_by_nct_id(self, repo):
        raw_json = {"data": "test"}
        repo.insert_study("NCT001", raw_json)

        results = repo.get_study_by_nct_id("NCT001")

        assert len(results) == 1
        assert results[0]["nct_id"] == "NCT001"
        assert results[0]["raw_json"] == raw_json

    def test_get_study_by_nct_id_not_found(self, repo):
        results = repo.get_study_by_nct_id("NCT999")
        assert results == []

    def test_get_latest_study(self, repo):
        repo.insert_study("NCT001", {"version": 1})
        repo.insert_study("NCT001", {"version": 2})

        latest = repo.get_latest_study("NCT001")

        assert latest is not None
        assert latest["raw_json"]["version"] == 2

    def test_get_latest_study_not_found(self, repo):
        result = repo.get_latest_study("NCT999")
        assert result is None

    def test_source_is_stored(self, repo):
        repo.insert_study("NCT001", {"data": "test"}, source="custom_source")

        results = repo.get_study_by_nct_id("NCT001")

        assert results[0]["source"] == "custom_source"
