"""Tests for ClinicalTrials.gov API client."""

import pytest
import requests

from clinical_trial_pipeline.extract.clinicaltrials_client import (
    APIConfig,
    ClinicalTrialsAPIError,
    ClinicalTrialsClient,
)


class TestAPIConfig:
    """Tests for APIConfig."""

    def test_default_values(self):
        config = APIConfig()
        assert config.base_url == "https://clinicaltrials.gov/api/v2"
        assert config.timeout == 30
        assert config.page_size == 100

    def test_custom_values(self):
        config = APIConfig(base_url="http://test.com", timeout=10, page_size=50)
        assert config.base_url == "http://test.com"
        assert config.timeout == 10
        assert config.page_size == 50


class TestClinicalTrialsClient:
    """Tests for ClinicalTrialsClient."""

    def test_fetch_studies_success(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "studies": [{"protocolSection": {"identificationModule": {"nctId": "NCT001"}}}],
            "nextPageToken": "token123",
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_session = mocker.patch("requests.Session")
        mock_session.return_value.get.return_value = mock_response

        with ClinicalTrialsClient() as client:
            data = client.fetch_studies(page_size=10)

        assert len(data["studies"]) == 1
        assert data["nextPageToken"] == "token123"
        mock_session.return_value.get.assert_called_once()

    def test_fetch_studies_with_page_token(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {"studies": [], "nextPageToken": None}
        mock_response.raise_for_status = mocker.Mock()

        mock_session = mocker.patch("requests.Session")
        mock_session.return_value.get.return_value = mock_response

        with ClinicalTrialsClient() as client:
            client.fetch_studies(page_token="abc123", page_size=50)

        call_kwargs = mock_session.return_value.get.call_args
        assert call_kwargs.kwargs["params"]["pageToken"] == "abc123"
        assert call_kwargs.kwargs["params"]["pageSize"] == 50

    def test_fetch_studies_timeout_error(self, mocker):
        mock_session = mocker.patch("requests.Session")
        mock_session.return_value.get.side_effect = requests.exceptions.Timeout()

        with ClinicalTrialsClient() as client:
            with pytest.raises(ClinicalTrialsAPIError) as exc_info:
                client.fetch_studies()

        assert "timed out" in str(exc_info.value)

    def test_fetch_studies_connection_error(self, mocker):
        mock_session = mocker.patch("requests.Session")
        mock_session.return_value.get.side_effect = requests.exceptions.ConnectionError()

        with ClinicalTrialsClient() as client:
            with pytest.raises(ClinicalTrialsAPIError) as exc_info:
                client.fetch_studies()

        assert "Failed to connect" in str(exc_info.value)

    def test_fetch_studies_http_error(self, mocker):
        mock_response = mocker.Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )

        mock_session = mocker.patch("requests.Session")
        mock_session.return_value.get.return_value = mock_response

        with ClinicalTrialsClient() as client:
            with pytest.raises(ClinicalTrialsAPIError) as exc_info:
                client.fetch_studies()

        assert "500" in str(exc_info.value)

    def test_context_manager(self, mocker):
        mock_session = mocker.patch("requests.Session")

        with ClinicalTrialsClient() as client:
            assert client._session is not None

        mock_session.return_value.close.assert_called_once()

    def test_custom_config(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {"studies": []}
        mock_response.raise_for_status = mocker.Mock()

        mock_session = mocker.patch("requests.Session")
        mock_session.return_value.get.return_value = mock_response

        config = APIConfig(base_url="http://custom.api", timeout=5, page_size=25)

        with ClinicalTrialsClient(config=config) as client:
            client.fetch_studies()

        call_kwargs = mock_session.return_value.get.call_args
        assert "http://custom.api/studies" in call_kwargs.args[0]
        assert call_kwargs.kwargs["timeout"] == 5
        assert call_kwargs.kwargs["params"]["pageSize"] == 25
