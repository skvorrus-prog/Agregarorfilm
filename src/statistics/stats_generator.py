"""Calculates release statistics, distributions, and quality metrics."""
from collections import defaultdict
from typing import List, Dict, Any
from src.models.movie import Movie


class StatsGenerator:
    """Generates aggregations and analytics over catalog data."""

    @staticmethod
    def generate(movies: List[Movie]) -> Dict[str, Any]:
        total_movies = len(movies)
        if total_movies == 0:
            return {
                "total_releases": 0,
                "web_dl_count": 0,
                "bluray_count": 0,
                "four_k_count": 0,
                "hdr_count": 0,
                "ru_audio_count": 0,
                "avg_rating": None,
                "by_year": {},
                "by_month": {},
                "by_quality": {},
                "by_genre": {},
            }

        quality_counts: Dict[str, int] = defaultdict(int)
        resolution_counts: Dict[str, int] = defaultdict(int)
        genre_counts: Dict[str, int] = defaultdict(int)
        year_counts: Dict[str, int] = defaultdict(int)
        month_counts: Dict[str, int] = defaultdict(int)

        four_k_count = 0
        hdr_count = 0
        ru_audio_count = 0

        rating_sum = 0.0
        rated_count = 0

        for m in movies:
            quality_counts[m.best_quality] += 1
            resolution_counts[m.best_resolution] += 1

            if m.has_4k:
                four_k_count += 1
            if m.has_hdr:
                hdr_count += 1
            if m.has_ru_audio:
                ru_audio_count += 1

            if m.imdb_rating is not None:
                rating_sum += m.imdb_rating
                rated_count += 1
            elif m.tmdb_rating is not None:
                rating_sum += m.tmdb_rating
                rated_count += 1

            # Year / Month
            date_str = m.digital_release_date or m.first_detected_at[:10]
            if date_str and len(date_str) >= 7:
                y = date_str[:4]
                ym = date_str[:7]
                year_counts[y] += 1
                month_counts[ym] += 1

            for g in m.genres:
                genre_counts[g] += 1

        avg_rating = round(rating_sum / rated_count, 2) if rated_count > 0 else None

        return {
            "total_releases": total_movies,
            "web_dl_count": quality_counts.get("WEB-DL", 0) + quality_counts.get("WEBRip", 0),
            "bluray_count": quality_counts.get("BluRay", 0) + quality_counts.get("REMUX", 0) + quality_counts.get("UHD BluRay", 0),
            "four_k_count": four_k_count,
            "hdr_count": hdr_count,
            "ru_audio_count": ru_audio_count,
            "avg_rating": avg_rating,
            "rated_movies_count": rated_count,
            "by_year": dict(sorted(year_counts.items(), reverse=True)),
            "by_month": dict(sorted(month_counts.items())),
            "by_quality": dict(sorted(quality_counts.items(), key=lambda x: x[1], reverse=True)),
            "by_resolution": dict(sorted(resolution_counts.items(), key=lambda x: x[1], reverse=True)),
            "by_genre": dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:12]),
        }
