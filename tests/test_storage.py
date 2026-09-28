"""Unit tests for SQLite repository, event saving, and first_detected_at preservation."""
import tempfile
from pathlib import Path
from src.models.movie import Movie
from src.models.release_event import ReleaseEvent
from src.storage.repository import MovieRepository


def test_repository_save_and_retrieve():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        repo = MovieRepository(db_path)

        movie = Movie(
            id="tt12345",
            title="Sample Movie",
            original_title="Original Sample",
            year=2024,
            imdb_id="tt12345",
            imdb_rating=8.1,
            imdb_vote_count=50000,
            digital_release_date="2024-09-28",
            first_detected_at="2024-09-28T10:00:00Z",
        )
        repo.save_movie(movie)

        ev = ReleaseEvent.create(
            movie_id=movie.id,
            source_name="TestSource",
            quality="WEB-DL",
            resolution="1080p",
            language="RU",
        )
        repo.save_event(ev)

        # Retrieve
        loaded = repo.get_movie("tt12345")
        assert loaded is not None
        assert loaded.title == "Sample Movie"
        assert loaded.imdb_rating == 8.1
        assert len(loaded.events) == 1
        assert loaded.events[0].quality == "WEB-DL"

        # Update movie with new rating, ensure first_detected_at is preserved
        movie.imdb_rating = 8.3
        movie.first_detected_at = "2024-09-29T10:00:00Z"  # attempt to change
        repo.save_movie(movie)

        reloaded = repo.get_movie("tt12345")
        assert reloaded.imdb_rating == 8.3
        assert reloaded.first_detected_at == "2024-09-28T10:00:00Z"  # preserved!

        repo.close()
