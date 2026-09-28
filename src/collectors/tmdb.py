"""The Movie Database (TMDB) API collector for official digital releases."""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from src.collectors.base import BaseSource, RawRelease, SourceResult
from src.models.enums import PipelineStatus
from src.config.settings import config


class TMDBDigitalSource(BaseSource):
    """Fetches official digital releases from TMDB API."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="TMDB", rate_limit_delay=0.3, timeout=10.0, max_retries=3)
        self.api_key = (api_key or config.tmdb_api_key or "").strip()

    def fetch_releases(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> SourceResult:
        if not self.api_key:
            return SourceResult(
                source_name=self.name,
                status=PipelineStatus.SUCCESS,
                releases=[],
                error_message="TMDB_API_KEY is not configured. TMDB source skipped.",
                items_count=0,
            )

        # Default to past 14 days if dates not specified
        today = datetime.now(timezone.utc).date()
        d_to = date_to or today.isoformat()
        d_from = date_from or (today - timedelta(days=14)).isoformat()

        releases: List[RawRelease] = []
        try:
            discover_url = "https://api.themoviedb.org/3/discover/movie"
            params = {
                "api_key": self.api_key,
                "with_release_type": "4",  # Digital releases
                "release_date.gte": d_from,
                "release_date.lte": d_to,
                "sort_by": "primary_release_date.desc",
                "vote_count.gte": 1,
            }

            resp = self._safe_request(discover_url, params=params)
            data = resp.json()
            results = data.get("results", [])

            # Process up to 25 items per run to respect polite limits
            for item in results[:25]:
                tmdb_id = item.get("id")
                if not tmdb_id:
                    continue

                details_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
                det_params = {
                    "api_key": self.api_key,
                    "append_to_response": "release_dates,external_ids",
                }
                try:
                    det_resp = self._safe_request(details_url, params=det_params)
                    det = det_resp.json()
                except Exception:
                    # Fallback to basic item if detailed call fails
                    det = item

                imdb_id = det.get("external_ids", {}).get("imdb_id")
                poster_path = det.get("poster_path")
                backdrop_path = det.get("backdrop_path")
                poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                backdrop = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None

                # Find exact digital release date from release_dates object
                digital_date = None
                rd_results = det.get("release_dates", {}).get("results", [])
                for country_entry in rd_results:
                    for r_entry in country_entry.get("release_dates", []):
                        if r_entry.get("type") == 4:  # 4 = Digital
                            raw_dt = r_entry.get("release_date")
                            if raw_dt:
                                digital_date = raw_dt.split("T")[0]
                                break
                    if digital_date:
                        break

                if not digital_date:
                    digital_date = det.get("release_date")

                raw_release = RawRelease(
                    raw_title=det.get("title") or item.get("title", ""),
                    source_name=self.name,
                    source_release_date=digital_date,
                    imdb_id=imdb_id,
                    tmdb_id=tmdb_id,
                    official_digital_date=digital_date,
                    parsed_title=det.get("title"),
                    parsed_original_title=det.get("original_title"),
                    parsed_year=int(digital_date[:4]) if digital_date else None,
                    metadata={
                        "overview": det.get("overview"),
                        "poster": poster,
                        "backdrop": backdrop,
                        "genres": [g["name"] for g in det.get("genres", []) if "name" in g],
                        "countries": [c["name"] for c in det.get("production_countries", []) if "name" in c],
                        "runtime": det.get("runtime"),
                        "popularity": det.get("popularity"),
                        "popularity_source": "TMDB",
                        "tmdb_rating": det.get("vote_average"),
                        "tmdb_vote_count": det.get("vote_count"),
                        "theatrical_release_date": det.get("release_date"),
                        "digital_release_date": digital_date,
                    }
                )
                releases.append(raw_release)

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
                releases=releases,
                error_message=str(exc),
                items_count=len(releases),
            )
