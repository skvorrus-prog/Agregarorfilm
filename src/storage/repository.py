"""Database repository for movies, release events, and historical rating tracking."""
import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Union

from src.models.movie import Movie
from src.models.release_event import ReleaseEvent
from src.storage.db import init_db


class MovieRepository:
    """Provides atomic, idempotent persistence for movies and events in SQLite."""

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = Path(db_path)
        self.conn = init_db(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def save_movie(self, movie: Movie) -> None:
        """Saves or updates movie, preserving earliest first_detected_at."""
        with self.conn:
            cursor = self.conn.cursor()
            # Check existing first_detected_at
            cursor.execute("SELECT first_detected_at FROM movies WHERE id = ?", (movie.id,))
            row = cursor.fetchone()
            first_detected = row["first_detected_at"] if row else movie.first_detected_at

            sql = """
            INSERT INTO movies (
                id, title, original_title, year, overview, poster, backdrop,
                genres, countries, runtime, imdb_id, tmdb_id,
                imdb_rating, imdb_vote_count, tmdb_rating, tmdb_vote_count,
                popularity, popularity_source, theatrical_release_date,
                digital_release_date, first_detected_at, last_updated_at,
                status, best_quality, best_resolution, has_4k, has_hdr, has_ru_audio
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                original_title = COALESCE(excluded.original_title, movies.original_title),
                year = COALESCE(excluded.year, movies.year),
                overview = COALESCE(excluded.overview, movies.overview),
                poster = COALESCE(excluded.poster, movies.poster),
                backdrop = COALESCE(excluded.backdrop, movies.backdrop),
                genres = excluded.genres,
                countries = excluded.countries,
                runtime = COALESCE(excluded.runtime, movies.runtime),
                imdb_id = COALESCE(excluded.imdb_id, movies.imdb_id),
                tmdb_id = COALESCE(excluded.tmdb_id, movies.tmdb_id),
                imdb_rating = COALESCE(excluded.imdb_rating, movies.imdb_rating),
                imdb_vote_count = COALESCE(excluded.imdb_vote_count, movies.imdb_vote_count),
                tmdb_rating = COALESCE(excluded.tmdb_rating, movies.tmdb_rating),
                tmdb_vote_count = COALESCE(excluded.tmdb_vote_count, movies.tmdb_vote_count),
                popularity = COALESCE(excluded.popularity, movies.popularity),
                popularity_source = COALESCE(excluded.popularity_source, movies.popularity_source),
                theatrical_release_date = COALESCE(excluded.theatrical_release_date, movies.theatrical_release_date),
                digital_release_date = COALESCE(excluded.digital_release_date, movies.digital_release_date),
                last_updated_at = excluded.last_updated_at,
                status = excluded.status,
                best_quality = excluded.best_quality,
                best_resolution = excluded.best_resolution,
                has_4k = excluded.has_4k,
                has_hdr = excluded.has_hdr,
                has_ru_audio = excluded.has_ru_audio;
            """
            cursor.execute(
                sql,
                (
                    movie.id,
                    movie.title,
                    movie.original_title,
                    movie.year,
                    movie.overview,
                    movie.poster,
                    movie.backdrop,
                    json.dumps(movie.genres, ensure_ascii=False),
                    json.dumps(movie.countries, ensure_ascii=False),
                    movie.runtime,
                    movie.imdb_id,
                    movie.tmdb_id,
                    movie.imdb_rating,
                    movie.imdb_vote_count,
                    movie.tmdb_rating,
                    movie.tmdb_vote_count,
                    movie.popularity,
                    movie.popularity_source,
                    movie.theatrical_release_date,
                    movie.digital_release_date,
                    first_detected,
                    movie.last_updated_at,
                    movie.status,
                    movie.best_quality,
                    movie.best_resolution,
                    1 if movie.has_4k else 0,
                    1 if movie.has_hdr else 0,
                    1 if movie.has_ru_audio else 0,
                )
            )

    def save_event(self, event: ReleaseEvent) -> bool:
        """Inserts release event idempotently. Returns True if newly added, False if duplicate."""
        with self.conn:
            cursor = self.conn.cursor()
            sql = """
            INSERT OR IGNORE INTO release_events (
                id, movie_id, event_type, source_name, source_release_date,
                detected_at, quality, resolution, hdr, audio, language,
                release_group, raw_title, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            cursor.execute(
                sql,
                (
                    event.id,
                    event.movie_id,
                    event.event_type,
                    event.source_name,
                    event.source_release_date,
                    event.detected_at,
                    event.quality,
                    event.resolution,
                    event.hdr,
                    event.audio,
                    event.language,
                    event.release_group,
                    event.raw_title,
                    json.dumps(event.details or {}, ensure_ascii=False),
                )
            )
            return cursor.rowcount > 0

    def get_events_for_movie(self, movie_id: str) -> List[ReleaseEvent]:
        """Loads all events for a given movie ordered chronologically."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM release_events
            WHERE movie_id = ?
            ORDER BY COALESCE(source_release_date, detected_at) ASC
            """,
            (movie_id,),
        )
        rows = cursor.fetchall()
        events = []
        for r in rows:
            details = json.loads(r["details"]) if r["details"] else None
            events.append(
                ReleaseEvent(
                    id=r["id"],
                    movie_id=r["movie_id"],
                    event_type=r["event_type"],
                    source_name=r["source_name"],
                    source_release_date=r["source_release_date"],
                    detected_at=r["detected_at"],
                    quality=r["quality"],
                    resolution=r["resolution"],
                    hdr=r["hdr"],
                    audio=r["audio"],
                    language=r["language"],
                    release_group=r["release_group"],
                    raw_title=r["raw_title"],
                    details=details,
                )
            )
        return events

    def _row_to_movie(self, row: sqlite3.Row, load_events: bool = True) -> Movie:
        genres = json.loads(row["genres"]) if row["genres"] else []
        countries = json.loads(row["countries"]) if row["countries"] else []
        events = self.get_events_for_movie(row["id"]) if load_events else []

        return Movie(
            id=row["id"],
            title=row["title"],
            original_title=row["original_title"],
            year=row["year"],
            overview=row["overview"],
            poster=row["poster"],
            backdrop=row["backdrop"],
            genres=genres,
            countries=countries,
            runtime=row["runtime"],
            imdb_id=row["imdb_id"],
            tmdb_id=row["tmdb_id"],
            imdb_rating=row["imdb_rating"],
            imdb_vote_count=row["imdb_vote_count"],
            tmdb_rating=row["tmdb_rating"],
            tmdb_vote_count=row["tmdb_vote_count"],
            popularity=row["popularity"],
            popularity_source=row["popularity_source"],
            theatrical_release_date=row["theatrical_release_date"],
            digital_release_date=row["digital_release_date"],
            first_detected_at=row["first_detected_at"],
            last_updated_at=row["last_updated_at"],
            status=row["status"],
            best_quality=row["best_quality"],
            best_resolution=row["best_resolution"],
            has_4k=bool(row["has_4k"]),
            has_hdr=bool(row["has_hdr"]),
            has_ru_audio=bool(row["has_ru_audio"]),
            events=events,
        )

    def get_movie(self, movie_id: str) -> Optional[Movie]:
        """Retrieves a movie by its unique identifier."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_movie(row, load_events=True)

    def get_all_movies(self, load_events: bool = False) -> List[Movie]:
        """Retrieves all movies currently in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM movies ORDER BY digital_release_date DESC, first_detected_at DESC")
        rows = cursor.fetchall()
        return [self._row_to_movie(r, load_events=load_events) for r in rows]

    def record_rating_snapshot(self, movie: Movie, date_str: str) -> None:
        """Records rating & popularity history entry for tracking metrics over time."""
        if movie.imdb_rating is None and movie.popularity is None:
            return
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO rating_history (
                    movie_id, recorded_date, imdb_rating, imdb_vote_count,
                    popularity, popularity_source
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    movie.id,
                    date_str,
                    movie.imdb_rating,
                    movie.imdb_vote_count,
                    movie.popularity,
                    movie.popularity_source,
                )
            )
