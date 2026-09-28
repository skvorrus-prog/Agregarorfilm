"""Exports historical snapshots and static JSON data for GitHub Pages."""
import json
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.models.movie import Movie
from src.config.settings import Settings, config


class HistoryExporter:
    """Generates daily historical archives (data/history/YYYY/MM/DD.json) and website static files."""

    def __init__(self, settings: Settings = config):
        self.settings = settings

    def export_all(self, movies: List[Movie], stats_data: Optional[Dict[str, Any]] = None) -> None:
        """Exports daily history archives and static website JSON files."""
        self.settings.ensure_directories()
        self.export_daily_history(movies)
        self.export_website_data(movies, stats_data)

    def export_daily_history(self, movies: List[Movie]) -> None:
        """
        Organizes releases by calendar date and saves snapshots:
        data/history/YYYY/MM/DD.json
        """
        by_date: Dict[str, List[Movie]] = defaultdict(list)

        for m in movies:
            # Group by digital_release_date if available, else date part of first_detected_at
            release_date = m.digital_release_date or m.first_detected_at[:10]
            if release_date and len(release_date) == 10:
                by_date[release_date].append(m)

        for date_str, day_movies in by_date.items():
            parts = date_str.split("-")
            if len(parts) != 3:
                continue
            year, month, day = parts[0], parts[1], parts[2]
            target_dir = self.settings.history_dir / year / month
            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / f"{day}.json"

            payload = {
                "date": date_str,
                "count": len(day_movies),
                "movies": [m.model_dump() for m in day_movies],
            }

            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

    def export_website_data(self, movies: List[Movie], stats_data: Optional[Dict[str, Any]] = None) -> None:
        """Generates static assets in website/data/ for GitHub Pages frontend."""
        web_data_dir = self.settings.website_data_dir
        web_data_dir.mkdir(parents=True, exist_ok=True)

        # 1. Full catalog for client-side search & filtering
        catalog_dump = [m.model_dump() for m in movies]
        with open(web_data_dir / "catalog.json", "w", encoding="utf-8") as f:
            json.dump(catalog_dump, f, ensure_ascii=False, indent=1)

        # 2. Latest releases (fast initial paint)
        sorted_latest = sorted(
            movies,
            key=lambda m: (m.digital_release_date or "", m.first_detected_at),
            reverse=True,
        )
        latest_dump = [m.model_dump() for m in sorted_latest[:60]]
        with open(web_data_dir / "latest.json", "w", encoding="utf-8") as f:
            json.dump(latest_dump, f, ensure_ascii=False, indent=1)

        # 3. Calendar index: map of { "YYYY-MM-DD": count }
        calendar_counts: Dict[str, int] = defaultdict(int)
        for m in movies:
            date_key = m.digital_release_date or m.first_detected_at[:10]
            if date_key and len(date_key) == 10:
                calendar_counts[date_key] += 1

        with open(web_data_dir / "calendar.json", "w", encoding="utf-8") as f:
            json.dump(calendar_counts, f, ensure_ascii=False, indent=1)

        # 4. "On this day" (В этот день): index by MM-DD -> { YYYY: [movie_summaries] }
        on_this_day: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
        for m in movies:
            date_key = m.digital_release_date or m.first_detected_at[:10]
            if date_key and len(date_key) == 10:
                y, mm, dd = date_key.split("-")
                day_key = f"{mm}-{dd}"
                summary = {
                    "id": m.id,
                    "title": m.title,
                    "original_title": m.original_title,
                    "year": m.year,
                    "poster": m.poster,
                    "digital_release_date": m.digital_release_date,
                    "imdb_rating": m.imdb_rating,
                    "imdb_vote_count": m.imdb_vote_count,
                    "best_quality": m.best_quality,
                    "best_resolution": m.best_resolution,
                    "has_4k": m.has_4k,
                    "has_hdr": m.has_hdr,
                    "has_ru_audio": m.has_ru_audio,
                }
                on_this_day[day_key][y].append(summary)

        with open(web_data_dir / "on_this_day.json", "w", encoding="utf-8") as f:
            json.dump(on_this_day, f, ensure_ascii=False, indent=1)

        # 5. Stats precalculated file
        if stats_data:
            with open(web_data_dir / "stats.json", "w", encoding="utf-8") as f:
                json.dump(stats_data, f, ensure_ascii=False, indent=2)
