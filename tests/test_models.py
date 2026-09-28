"""Unit tests for Movie and ReleaseEvent models and aggregate calculation."""
from src.models.movie import Movie
from src.models.release_event import ReleaseEvent
from src.models.enums import QualityType, Resolution, ReleaseStatus


def test_movie_id_generation():
    # Prefer imdb_id
    id1 = Movie.generate_id(imdb_id="tt1234567", title="Test Movie", year=2024)
    assert id1 == "tt1234567"

    # Fallback to tmdb_id
    id2 = Movie.generate_id(tmdb_id=98765, title="Test Movie", year=2024)
    assert id2 == "tmdb_98765"

    # Fallback to hash
    id3 = Movie.generate_id(title="Unique Movie", year=2024)
    assert id3.startswith("m_")


def test_movie_aggregate_updates():
    movie = Movie(id="test_1", title="Test Film", year=2024)
    assert movie.has_4k is False
    assert movie.has_hdr is False
    assert movie.best_resolution == "unknown"

    ev1 = ReleaseEvent.create(
        movie_id=movie.id,
        source_name="TestSource",
        quality="WEB-DL",
        resolution="1080p",
        language="RU",
    )
    assert movie.add_event(ev1) is True
    assert movie.best_quality == "WEB-DL"
    assert movie.best_resolution == "1080p"
    assert movie.has_ru_audio is True
    assert movie.status == ReleaseStatus.WEB_RELEASE.value

    # Upgrade to 2160p HDR
    ev2 = ReleaseEvent.create(
        movie_id=movie.id,
        source_name="TestSource",
        quality="WEB-DL",
        resolution="2160p",
        hdr="Dolby Vision",
        language="EN",
    )
    assert movie.add_event(ev2) is True
    assert movie.best_resolution == "2160p"
    assert movie.has_4k is True
    assert movie.has_hdr is True
    assert movie.status == ReleaseStatus.UHD_RELEASE.value

    # Re-adding exact same event is idempotent
    assert movie.add_event(ev2) is False
