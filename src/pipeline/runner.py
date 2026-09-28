"""Main pipeline orchestrating collectors, matching, storage, stats, and export."""
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.collectors.base import BaseSource, RawRelease
from src.collectors.tmdb import TMDBDigitalSource
from src.collectors.cinemeta import CinemetaSource
from src.collectors.release_rss import ReleaseRSSSource
from src.matching.movie_matcher import MovieMatcher
from src.models.enums import PipelineStatus, EventType, QualityType, Resolution
from src.models.movie import Movie
from src.models.release_event import ReleaseEvent
from src.normalizers.release_parser import ReleaseParser
from src.pipeline.telegram import TelegramNotifier
from src.statistics.stats_generator import StatsGenerator
from src.storage.history_exporter import HistoryExporter
from src.storage.repository import MovieRepository
from src.config.settings import Settings, config

logger = logging.getLogger(__name__)


class PipelineRunner:
    """End-to-end pipeline coordinator with idempotent runs and status reporting."""

    def __init__(
        self,
        repository: Optional[MovieRepository] = None,
        sources: Optional[List[BaseSource]] = None,
        settings: Settings = config,
    ):
        self.settings = settings
        self.settings.ensure_directories()
        self.repo = repository or MovieRepository(settings.database_path)
        self.sources = sources or [
            TMDBDigitalSource(),
            CinemetaSource(),
            ReleaseRSSSource(),
        ]
        self.exporter = HistoryExporter(settings)
        self.notifier = TelegramNotifier(settings)

    def run(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes full data collection, normalization, matching, storage, and build."""
        start_time = datetime.now(timezone.utc)
        logger.info(f"Pipeline started at {start_time.isoformat()}")

        # 1. Load existing movies and prime matcher
        existing_movies = self.repo.get_all_movies(load_events=True)
        matcher = MovieMatcher(existing_movies)
        logger.info(f"Loaded {len(existing_movies)} existing movies into matcher.")

        # 2. Collect raw releases from all sources
        source_summaries = {}
        all_raw_releases: List[RawRelease] = []
        overall_status = PipelineStatus.SUCCESS
        any_success = False

        for src in self.sources:
            try:
                res = src.fetch_releases(date_from=date_from, date_to=date_to)
                source_summaries[src.name] = {
                    "status": res.status.value,
                    "count": res.items_count,
                    "error": res.error_message,
                }
                if res.status in (PipelineStatus.SUCCESS, PipelineStatus.PARTIAL_SUCCESS):
                    any_success = True
                    all_raw_releases.extend(res.releases)
                if res.status == PipelineStatus.FAILED:
                    overall_status = PipelineStatus.PARTIAL_SUCCESS
            except Exception as e:
                logger.error(f"Source {src.name} unhandled exception: {e}")
                source_summaries[src.name] = {
                    "status": PipelineStatus.FAILED.value,
                    "count": 0,
                    "error": str(e),
                }
                overall_status = PipelineStatus.PARTIAL_SUCCESS

        if not any_success and self.sources:
            overall_status = PipelineStatus.FAILED

        # 3. Process, match, and normalize
        new_movies: List[Movie] = []
        new_events_count = 0
        current_date_str = start_time.date().isoformat()

        for raw in all_raw_releases:
            # Parse release details if not already structured
            parsed = ReleaseParser.parse(raw.raw_title)
            title = raw.parsed_title or parsed.title
            orig_title = raw.parsed_original_title or parsed.original_title
            year = raw.parsed_year or parsed.year

            quality = raw.metadata.get("quality") or parsed.quality
            resolution = raw.metadata.get("resolution") or parsed.resolution
            hdr = raw.metadata.get("hdr") or parsed.hdr
            audio = raw.metadata.get("audio") or parsed.audio
            language = raw.metadata.get("language") or parsed.language
            group = raw.metadata.get("release_group") or parsed.release_group

            # Match against existing catalog
            match = matcher.find_match(
                title=title,
                original_title=orig_title,
                year=year,
                imdb_id=raw.imdb_id,
                tmdb_id=raw.tmdb_id,
            )

            if match:
                movie = match
                # Update movie fields if new richer data is provided
                if not movie.imdb_id and raw.imdb_id:
                    movie.imdb_id = raw.imdb_id
                if not movie.tmdb_id and raw.tmdb_id:
                    movie.tmdb_id = raw.tmdb_id
                if not movie.original_title and orig_title:
                    movie.original_title = orig_title
                if not movie.year and year:
                    movie.year = year
                if not movie.poster and raw.metadata.get("poster"):
                    movie.poster = raw.metadata["poster"]
                if not movie.backdrop and raw.metadata.get("backdrop"):
                    movie.backdrop = raw.metadata["backdrop"]
                if not movie.overview and raw.metadata.get("overview"):
                    movie.overview = raw.metadata["overview"]
                if not movie.genres and raw.metadata.get("genres"):
                    movie.genres = raw.metadata["genres"]
                if not movie.countries and raw.metadata.get("countries"):
                    movie.countries = raw.metadata["countries"]
                if not movie.runtime and raw.metadata.get("runtime"):
                    movie.runtime = raw.metadata["runtime"]

                # Ratings & Popularity
                if raw.metadata.get("imdb_rating") is not None:
                    movie.imdb_rating = raw.metadata["imdb_rating"]
                if raw.metadata.get("imdb_vote_count") is not None:
                    movie.imdb_vote_count = raw.metadata["imdb_vote_count"]
                if raw.metadata.get("popularity") is not None:
                    movie.popularity = raw.metadata["popularity"]
                    movie.popularity_source = raw.metadata.get("popularity_source", "TMDB")
                if raw.metadata.get("tmdb_rating") is not None:
                    movie.tmdb_rating = raw.metadata["tmdb_rating"]
                if raw.metadata.get("tmdb_vote_count") is not None:
                    movie.tmdb_vote_count = raw.metadata["tmdb_vote_count"]

                # Digital release date
                if not movie.digital_release_date and raw.official_digital_date:
                    movie.digital_release_date = raw.official_digital_date

            else:
                # Create brand new movie
                movie_id = Movie.generate_id(
                    imdb_id=raw.imdb_id,
                    tmdb_id=raw.tmdb_id,
                    title=title,
                    year=year,
                )
                movie = Movie(
                    id=movie_id,
                    title=title,
                    original_title=orig_title,
                    year=year,
                    overview=raw.metadata.get("overview"),
                    poster=raw.metadata.get("poster"),
                    backdrop=raw.metadata.get("backdrop"),
                    genres=raw.metadata.get("genres") or [],
                    countries=raw.metadata.get("countries") or [],
                    runtime=raw.metadata.get("runtime"),
                    imdb_id=raw.imdb_id,
                    tmdb_id=raw.tmdb_id,
                    imdb_rating=raw.metadata.get("imdb_rating"),
                    imdb_vote_count=raw.metadata.get("imdb_vote_count"),
                    tmdb_rating=raw.metadata.get("tmdb_rating"),
                    tmdb_vote_count=raw.metadata.get("tmdb_vote_count"),
                    popularity=raw.metadata.get("popularity"),
                    popularity_source=raw.metadata.get("popularity_source"),
                    theatrical_release_date=raw.metadata.get("theatrical_release_date"),
                    digital_release_date=raw.official_digital_date or raw.metadata.get("digital_release_date"),
                    first_detected_at=start_time.isoformat(),
                    last_updated_at=start_time.isoformat(),
                )
                matcher.register(movie)
                new_movies.append(movie)

            # Determine event type
            if raw.official_digital_date:
                event_type = EventType.DIGITAL_PREMIERE.value
            elif resolution == Resolution.RES_2160P.value or "2160p" in (raw.raw_title or ""):
                event_type = EventType.UHD_DETECTED.value
            elif language == "RU":
                event_type = EventType.RU_AUDIO_DETECTED.value
            elif quality in (QualityType.BLURAY.value, QualityType.REMUX.value):
                event_type = EventType.BLURAY_DETECTED.value
            elif quality in (QualityType.WEB_DL.value, QualityType.WEB_RIP.value):
                event_type = EventType.WEB_DL_DETECTED.value
            else:
                event_type = EventType.RELEASE_DETECTED.value

            # Create event
            ev = ReleaseEvent.create(
                movie_id=movie.id,
                source_name=raw.source_name,
                event_type=event_type,
                quality=quality,
                resolution=resolution,
                hdr=hdr,
                audio=audio,
                language=language,
                release_group=group,
                source_release_date=raw.source_release_date,
                detected_at=start_time.isoformat(),
                raw_title=raw.raw_title,
                details=raw.metadata,
            )

            if movie.add_event(ev):
                new_events_count += 1

            # Persist to database
            self.repo.save_movie(movie)
            self.repo.save_event(ev)
            self.repo.record_rating_snapshot(movie, current_date_str)

        # 4. Generate statistics & export history
        all_movies = self.repo.get_all_movies(load_events=True)
        stats = StatsGenerator.generate(all_movies)
        self.exporter.export_all(all_movies, stats)

        # 5. Notify new releases
        notified_count = 0
        if new_movies:
            notified_count = self.notifier.notify_new_releases(new_movies)

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"Pipeline finished: status={overall_status.value}, "
            f"total_movies={len(all_movies)}, new_movies={len(new_movies)}, "
            f"new_events={new_events_count}, time={duration:.2f}s"
        )

        return {
            "status": overall_status.value,
            "duration_seconds": round(duration, 2),
            "total_movies": len(all_movies),
            "new_movies_count": len(new_movies),
            "new_events_count": new_events_count,
            "notified_count": notified_count,
            "sources": source_summaries,
            "stats": stats,
        }
