"""Base adapter class for data collectors with rate limiting and exponential backoff."""
import time
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import requests
from pydantic import BaseModel, Field

from src.models.enums import PipelineStatus


class RawRelease(BaseModel):
    """Raw release item produced by any collector adapter."""
    raw_title: str
    source_name: str
    source_release_date: Optional[str] = None
    imdb_id: Optional[str] = None
    tmdb_id: Optional[int] = None
    official_digital_date: Optional[str] = None
    parsed_title: Optional[str] = None
    parsed_original_title: Optional[str] = None
    parsed_year: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceResult(BaseModel):
    """Result summary of a collector invocation."""
    source_name: str
    status: PipelineStatus
    releases: List[RawRelease] = Field(default_factory=list)
    error_message: Optional[str] = None
    items_count: int = 0


class BaseSource(ABC):
    """Abstract collector adapter."""

    def __init__(
        self,
        name: str,
        rate_limit_delay: float = 0.5,
        timeout: float = 12.0,
        max_retries: int = 3,
    ):
        self.name = name
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.max_retries = max_retries
        self._last_request_time = 0.0

    def _apply_rate_limit(self) -> None:
        """Enforces rate limit delay between successive requests."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def _safe_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Executes HTTP request with exponential backoff and error handling."""
        default_headers = {
            "User-Agent": "DigitalMovieReleases/1.0 (Automated Collector; Open-Source)",
            "Accept": "application/json, application/xml, text/xml, */*",
        }
        if headers:
            default_headers.update(headers)

        last_exception = None
        for attempt in range(self.max_retries):
            try:
                self._apply_rate_limit()
                response = requests.get(
                    url,
                    params=params,
                    headers=default_headers,
                    timeout=self.timeout,
                )
                if response.status_code == 429:
                    # Rate limited: wait longer
                    time.sleep(2.0 * (attempt + 1))
                    continue
                response.raise_for_status()
                return response
            except Exception as exc:
                last_exception = exc
                wait_time = (2 ** attempt) * 0.5
                time.sleep(wait_time)

        raise RuntimeError(f"Request failed for {url} after {self.max_retries} attempts: {last_exception}")

    @abstractmethod
    def fetch_releases(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> SourceResult:
        """Fetches releases within optional date window."""
        pass
