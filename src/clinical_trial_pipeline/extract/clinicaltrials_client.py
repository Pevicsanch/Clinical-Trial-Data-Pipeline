"""ClinicalTrials.gov API v2 client."""

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


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
        self._client = httpx.Client(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )

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

        logger.debug("Fetching studies with params: %s", params)

        try:
            response = self._client.get("/studies", params=params)
            response.raise_for_status()
        except httpx.TimeoutException as e:
            raise ClinicalTrialsAPIError(
                f"Request timed out after {self.config.timeout}s"
            ) from e
        except httpx.ConnectError as e:
            raise ClinicalTrialsAPIError(
                f"Failed to connect to {self.config.base_url}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise ClinicalTrialsAPIError(
                f"API returned status {e.response.status_code}: {e.response.text[:200]}"
            ) from e

        data = response.json()
        study_count = len(data.get("studies", []))
        logger.info("Fetched %d studies", study_count)

        return data

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
