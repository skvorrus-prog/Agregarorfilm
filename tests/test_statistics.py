"""Unit tests for statistics generator."""
from src.models.movie import Movie
from src.statistics.stats_generator import StatsGenerator


def test_statistics_aggregation():
    m1 = Movie(
        id="m1",
        title="Movie 1",
        digital_release_date="2026-09-28",
        best_quality="WEB-DL",
        best_resolution="2160p",
        has_4k=True,
        has_hdr=True,
        has_ru_audio=True,
        imdb_rating=8.0,
        genres=["Action", "Sci-Fi"],
    )
    m2 = Movie(
        id="m2",
        title="Movie 2",
        digital_release_date="2026-09-28",
        best_quality="BluRay",
        best_resolution="1080p",
        has_4k=False,
        has_hdr=False,
        has_ru_audio=False,
        imdb_rating=6.0,
        genres=["Drama"],
    )
    m3 = Movie(
        id="m3",
        title="Movie 3",
        digital_release_date="2026-08-15",
        best_quality="WEB-DL",
        best_resolution="1080p",
        has_4k=False,
        has_hdr=False,
        has_ru_audio=True,
        imdb_rating=None,  # Unknown rating should not break average!
        genres=["Action"],
    )

    stats = StatsGenerator.generate([m1, m2, m3])
    assert stats["total_releases"] == 3
    assert stats["web_dl_count"] == 2
    assert stats["bluray_count"] == 1
    assert stats["four_k_count"] == 1
    assert stats["hdr_count"] == 1
    assert stats["ru_audio_count"] == 2
    assert stats["avg_rating"] == 7.0  # (8.0 + 6.0) / 2
    assert stats["by_month"]["2026-09"] == 2
    assert stats["by_month"]["2026-08"] == 1
    assert stats["by_genre"]["Action"] == 2
