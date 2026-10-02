"""Cinemeta open metadata collector providing IMDb data without API keys."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from src.collectors.base import BaseSource, RawRelease, SourceResult
from src.models.enums import PipelineStatus


class CinemetaSource(BaseSource):
    """Collector fetching popular releases and IMDb metadata via Cinemeta open API."""

    def __init__(self):
        super().__init__(name="Cinemeta", rate_limit_delay=0.4, timeout=10.0, max_retries=3)

    def fetch_releases(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> SourceResult:
        catalog_url = "https://v3-cinemeta.strem.io/catalog/movie/top.json"
        releases: List[RawRelease] = []

        try:
            resp = self._safe_request(catalog_url)
            data = resp.json()
            metas = data.get("metas", [])

            current_year = datetime.now(timezone.utc).year

            # Filter for recent movies (current year or previous year)
            for m in metas:
                raw_year = m.get("year")
                try:
                    year_val = int(str(raw_year)[:4]) if raw_year else None
                except ValueError:
                    year_val = None

                # Keep recent movies
                if year_val and year_val < (current_year - 2):
                    continue

                imdb_id = m.get("id")
                name = m.get("name")
                if not name or not imdb_id:
                    continue

                raw_release = RawRelease(
                    raw_title=f"{name} ({year_val or ''})",
                    source_name=self.name,
                    source_release_date=None,
                    imdb_id=imdb_id,
                    parsed_title=name,
                    parsed_original_title=name,
                    parsed_year=year_val,
                    metadata={
                        "title": name,
                        "year": year_val,
                        "overview": m.get("description"),
                        "poster": m.get("poster"),
                        "genres": m.get("genres") if isinstance(m.get("genres"), list) else [m.get("genres")] if m.get("genres") else [],
                        "countries": [m.get("country")] if m.get("country") else [],
                        "imdb_rating": float(m.get("imdbRating")) if m.get("imdbRating") else None,
                        "runtime": None,
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

    def fetch_movie_detail(self, imdb_id: str) -> Optional[Dict[str, Any]]:
        """Fetches detailed IMDb metadata for a specific IMDb ID."""
        if not imdb_id or not imdb_id.startswith("tt"):
            return None
        url = f"https://v3-cinemeta.strem.io/meta/movie/{imdb_id}.json"
        try:
            resp = self._safe_request(url)
            meta = resp.json().get("meta", {})
            return {
                "title": meta.get("name"),
                "year": int(meta.get("year")) if meta.get("year") else None,
                "overview": meta.get("description"),
                "poster": meta.get("poster"),
                "genres": meta.get("genres") if isinstance(meta.get("genres"), list) else [],
                "countries": [meta.get("country")] if meta.get("country") else [],
                "imdb_rating": float(meta.get("imdbRating")) if meta.get("imdbRating") else None,
                "runtime": int(str(meta.get("runtime", "")).replace("min", "").strip()) if meta.get("runtime") else None,
            }
        except Exception:
            return None

    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Searches Cinemeta by title/year to enrich releases with IMDb posters, IDs and metadata."""
        if not title or len(title.strip()) < 2:
            return None

        import urllib.parse
        clean_title = title.strip()
        encoded = urllib.parse.quote(clean_title)
        url = f"https://v3-cinemeta.strem.io/catalog/movie/top/search={encoded}.json"

        try:
            resp = self._safe_request(url)
            metas = resp.json().get("metas", [])
            if not metas:
                return None

            best_meta = None
            best_score = 0.0
            from src.normalizers.title_normalizer import title_similarity, normalize_title
            clean_norm = normalize_title(clean_title)

            for m in metas:
                m_name = m.get("name")
                if not m_name:
                    continue

                # Check year compatibility if specified
                m_year = m.get("year")
                try:
                    y_int = int(str(m_year)[:4]) if m_year else None
                    if year and y_int and abs(y_int - year) > 1:
                        continue
                except Exception:
                    pass

                # Exact normalized title match gets highest score
                if normalize_title(m_name) == clean_norm:
                    score = 1.0
                else:
                    score = title_similarity(clean_title, m_name)

                # Require high similarity (>= 0.70) to prevent false positives
                if score >= 0.70 and score > best_score:
                    best_score = score
                    best_meta = m
                    if score == 1.0:
                        break

            if not best_meta:
                return None

            imdb_id = best_meta.get("id") or best_meta.get("imdb_id")
            poster = best_meta.get("poster")
            name = best_meta.get("name")

            # If search item doesn't have full details, fetch detail
            detail = self.fetch_movie_detail(imdb_id) if imdb_id else None

            return {
                "imdb_id": imdb_id,
                "title": name,
                "year": detail.get("year") if detail else year,
                "poster": poster or (detail.get("poster") if detail else None),
                "overview": detail.get("overview") if detail else None,
                "genres": detail.get("genres") if detail else (best_meta.get("genres") or []),
                "countries": detail.get("countries") if detail else [],
                "imdb_rating": detail.get("imdb_rating") if detail else (float(best_meta.get("imdbRating")) if best_meta.get("imdbRating") else None),
            }
        except Exception:
            return None
