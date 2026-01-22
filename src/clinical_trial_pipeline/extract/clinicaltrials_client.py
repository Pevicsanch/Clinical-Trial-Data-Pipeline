"""ClinicalTrials.gov API v2 client."""

from dataclasses import dataclass
from typing import Any

import requests

from clinical_trial_pipeline.common.logging import get_logger

logger = get_logger(__name__)


@dataclass
class APIConfig:
    """API client configuration."""

    base_url: str = "https://clinicaltrials.gov/api/v2"
    timeout: int = 30
    page_size: int = 100


class ClinicalTrialsAPIError(Exception):
    """Raised when API request fails."""

    pass


class ClinicalTrialsClient:
    """Client for ClinicalTrials.gov API v2."""

    def __init__(self, config: APIConfig | None = None):
        self.config = config or APIConfig()
        self._session = requests.Session()

    def fetch_studies(
        self,
        page_token: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """Fetch a page of studies from the API."""
        params = {
            "pageSize": page_size or self.config.page_size,
        }
        if page_token:
            params["pageToken"] = page_token

        url = f"{self.config.base_url}/studies"
        logger.debug("Fetching studies from %s with params: %s", url, params)

        try:
            response = self._session.get(
                url,
                params=params,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as e:
            raise ClinicalTrialsAPIError(
                f"Request timed out after {self.config.timeout}s"
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise ClinicalTrialsAPIError(
                f"Failed to connect to {self.config.base_url}"
            ) from e
        except requests.exceptions.HTTPError as e:
            raise ClinicalTrialsAPIError(
                f"API returned status {e.response.status_code}: {e.response.text[:200]}"
            ) from e

        data = response.json()
        study_count = len(data.get("studies", []))
        logger.info("Fetched %d studies", study_count)

        return data

    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
