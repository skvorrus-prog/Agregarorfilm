"""Fixture collector for testing, deterministic offline runs, and backfills."""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.collectors.base import BaseSource, RawRelease, SourceResult
from src.models.enums import PipelineStatus


class FixtureSource(BaseSource):
    """Loads releases from a static JSON fixture file."""

    def __init__(self, fixture_path: Optional[Path] = None):
        super().__init__(name="Fixture", rate_limit_delay=0.0, timeout=1.0, max_retries=1)
        self.fixture_path = fixture_path

    def fetch_releases(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> SourceResult:
        if not self.fixture_path or not self.fixture_path.exists():
            return SourceResult(
                source_name=self.name,
                status=PipelineStatus.SUCCESS,
                releases=[],
                error_message="Fixture file not found or path not specified",
                items_count=0,
            )

        try:
            with open(self.fixture_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            releases: List[RawRelease] = []
            for item in data:
                raw = RawRelease(
                    raw_title=item.get("raw_title", ""),
                    source_name=self.name,
                    source_release_date=item.get("source_release_date"),
                    imdb_id=item.get("imdb_id"),
                    tmdb_id=item.get("tmdb_id"),
                    official_digital_date=item.get("official_digital_date"),
                    parsed_title=item.get("parsed_title"),
                    parsed_original_title=item.get("parsed_original_title"),
                    parsed_year=item.get("parsed_year"),
                    metadata=item.get("metadata", {}),
                )
                releases.append(raw)

            return SourceResult(
                source_name=self.name,
                status=PipelineStatus.SUCCESS,
                releases=releases,
                items_count=len(releases),
            )
        except Exception as exc:
            return SourceResult(
                source_name=self.name,
                status=PipelineStatus.FAILED,
                releases=[],
                error_message=str(exc),
                items_count=0,
            )
