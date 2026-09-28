"""SQLite database initialization and connection management."""
import sqlite3
from pathlib import Path
from typing import Union

SCHEMA = """
CREATE TABLE IF NOT EXISTS movies (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    original_title TEXT,
    year INTEGER,
    overview TEXT,
    poster TEXT,
    backdrop TEXT,
    genres TEXT,
    countries TEXT,
    runtime INTEGER,
    imdb_id TEXT,
    tmdb_id INTEGER,
    imdb_rating REAL,
    imdb_vote_count INTEGER,
    tmdb_rating REAL,
    tmdb_vote_count INTEGER,
    popularity REAL,
    popularity_source TEXT,
    theatrical_release_date TEXT,
    digital_release_date TEXT,
    first_detected_at TEXT NOT NULL,
    last_updated_at TEXT NOT NULL,
    status TEXT NOT NULL,
    best_quality TEXT NOT NULL,
    best_resolution TEXT NOT NULL,
    has_4k INTEGER NOT NULL DEFAULT 0,
    has_hdr INTEGER NOT NULL DEFAULT 0,
    has_ru_audio INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_movies_imdb_id ON movies (imdb_id);
CREATE INDEX IF NOT EXISTS idx_movies_tmdb_id ON movies (tmdb_id);
CREATE INDEX IF NOT EXISTS idx_movies_digital_date ON movies (digital_release_date);
CREATE INDEX IF NOT EXISTS idx_movies_detected_at ON movies (first_detected_at);
CREATE INDEX IF NOT EXISTS idx_movies_status ON movies (status);

CREATE TABLE IF NOT EXISTS release_events (
    id TEXT PRIMARY KEY,
    movie_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_release_date TEXT,
    detected_at TEXT NOT NULL,
    quality TEXT NOT NULL,
    resolution TEXT NOT NULL,
    hdr TEXT,
    audio TEXT,
    language TEXT,
    release_group TEXT,
    raw_title TEXT,
    details TEXT,
    FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_events_movie_id ON release_events (movie_id);
CREATE INDEX IF NOT EXISTS idx_events_detected_at ON release_events (detected_at);

CREATE TABLE IF NOT EXISTS rating_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id TEXT NOT NULL,
    recorded_date TEXT NOT NULL,
    imdb_rating REAL,
    imdb_vote_count INTEGER,
    popularity REAL,
    popularity_source TEXT,
    FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE,
    UNIQUE(movie_id, recorded_date)
);

CREATE INDEX IF NOT EXISTS idx_rating_hist_movie_date ON rating_history (movie_id, recorded_date);
"""


def init_db(db_path: Union[str, Path]) -> sqlite3.Connection:
    """Initializes SQLite database tables and indexes."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    with conn:
        conn.executescript(SCHEMA)
    return conn
