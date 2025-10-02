"""ClinicalTrials.gov API client with caching."""

import json
import time
from pathlib import Path
from typing import Any, Optional

import requests

from trials.config import config


class ClinicalTrialsClient:
    """Client for ClinicalTrials.gov v2 API."""

    def __init__(
        self,
        base_url: str = config.API_BASE_URL,
        rate_limit_delay: float = config.RATE_LIMIT_DELAY,
        cache_dir: Optional[Path] = None,
    ):
        """Initialize the API client.

        Args:
            base_url: Base URL for the API
            rate_limit_delay: Delay between requests in seconds
            cache_dir: Directory for caching responses
        """
        self.base_url = base_url.rstrip("/")
        self.rate_limit_delay = rate_limit_delay
        self.cache_dir = cache_dir or config.RAW_DATA_DIR / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "nlp-insights/0.1.0 (Research; Python requests)",
                "Accept": "application/json",
            }
        )

    def _get_cache_path(self, cache_key: str) -> Path:
        """Generate cache file path for a given key."""
        safe_key = "".join(c if c.isalnum() or c in "-_" else "_" for c in cache_key)
        return self.cache_dir / f"{safe_key}.json"

    def _read_cache(self, cache_key: str) -> Optional[dict[str, Any]]:
        """Read cached response if available."""
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def _write_cache(self, cache_key: str, data: dict[str, Any]) -> None:
        """Write response to cache."""
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass  # Fail silently if cache write fails

    def search_studies(
        self,
        query: Optional[str] = None,
        condition: Optional[str] = None,
        page_size: int = 100,
        page_token: Optional[str] = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Search for clinical studies.

        Args:
            query: Free-text search query
            condition: Disease or condition
            page_size: Number of results per page (max 1000)
            page_token: Token for pagination
            use_cache: Whether to use cached responses

        Returns:
            API response with studies and pagination info
        """
        # Build query parameters
        params: dict[str, Any] = {"format": "json", "pageSize": min(page_size, 1000)}

        # Build query string
        query_parts = []
        if query:
            query_parts.append(query)
        if condition:
            query_parts.append(f"AREA[Condition]{condition}")

        if query_parts:
            params["query.cond"] = condition if condition else ""
            if query:
                params["query.term"] = query

        if page_token:
            params["pageToken"] = page_token

        # Generate cache key
        cache_key = f"search_{json.dumps(params, sort_keys=True)}"

        # Check cache
        if use_cache:
            cached = self._read_cache(cache_key)
            if cached is not None:
                return cached

        # Make request
        url = f"{self.base_url}/studies"
        time.sleep(self.rate_limit_delay)

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Cache response
        if use_cache:
            self._write_cache(cache_key, data)

        return data

    def get_study(self, nct_id: str, use_cache: bool = True) -> dict[str, Any]:
        """Get detailed information for a single study.

        Args:
            nct_id: NCT identifier (e.g., "NCT12345678")
            use_cache: Whether to use cached responses

        Returns:
            Study data
        """
        cache_key = f"study_{nct_id}"

        # Check cache
        if use_cache:
            cached = self._read_cache(cache_key)
            if cached is not None:
                return cached

        # Make request
        url = f"{self.base_url}/studies/{nct_id}"
        time.sleep(self.rate_limit_delay)

        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Cache response
        if use_cache:
            self._write_cache(cache_key, data)

        return data

    def search_all(
        self,
        query: Optional[str] = None,
        condition: Optional[str] = None,
        max_studies: Optional[int] = None,
        page_size: int = 1000,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """Search and retrieve all matching studies with pagination.

        Args:
            query: Free-text search query
            condition: Disease or condition
            max_studies: Maximum number of studies to retrieve
            page_size: Number of results per page
            use_cache: Whether to use cached responses

        Returns:
            List of all matching studies
        """
        all_studies = []
        next_page_token = None
        total_fetched = 0

        while True:
            response = self.search_studies(
                query=query,
                condition=condition,
                page_size=page_size,
                page_token=next_page_token,
                use_cache=use_cache,
            )

            studies = response.get("studies", [])
            all_studies.extend(studies)
            total_fetched += len(studies)

            print(
                f"Fetched {total_fetched} studies"
                + (f" (limit: {max_studies})" if max_studies else "")
            )

            # Check if we should continue
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
            if max_studies and total_fetched >= max_studies:
                all_studies = all_studies[:max_studies]
                break

        return all_studies
