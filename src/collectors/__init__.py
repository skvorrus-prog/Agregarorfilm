"""Collectors package with adapter interfaces."""
from src.collectors.base import BaseSource, RawRelease, SourceResult
from src.collectors.tmdb import TMDBDigitalSource
from src.collectors.cinemeta import CinemetaSource
from src.collectors.release_rss import ReleaseRSSSource
from src.collectors.fixture import FixtureSource

__all__ = [
    "BaseSource",
    "RawRelease",
    "SourceResult",
    "TMDBDigitalSource",
    "CinemetaSource",
    "ReleaseRSSSource",
    "FixtureSource",
]
