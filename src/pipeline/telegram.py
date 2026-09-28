"""Telegram notification service for newly detected digital releases."""
import logging
from typing import Optional, List
import requests

from src.models.movie import Movie
from src.config.settings import Settings, config

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Sends release notifications to a Telegram chat if credentials are provided."""

    def __init__(self, settings: Settings = config):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.enabled = bool(self.bot_token and self.chat_id)

    def format_movie_message(self, movie: Movie) -> str:
        """Constructs a clean Telegram message for a digital release."""
        orig = f" ({movie.original_title})" if movie.original_title and movie.original_title != movie.title else ""
        year_str = f" [{movie.year}]" if movie.year else ""

        rating_str = f"⭐ IMDb: {movie.imdb_rating}" if movie.imdb_rating is not None else "⭐ IMDb: —"
        if movie.imdb_vote_count:
            rating_str += f" ({movie.imdb_vote_count:,} голосов)"

        pop_str = f"🔥 Популярность: {movie.popularity} ({movie.popularity_source or 'TMDB'})" if movie.popularity else ""

        tags = []
        if movie.best_quality != "unknown":
            tags.append(movie.best_quality)
        if movie.best_resolution != "unknown":
            tags.append(movie.best_resolution)
        if movie.has_4k:
            tags.append("4K")
        if movie.has_hdr:
            tags.append("HDR")
        if movie.has_ru_audio:
            tags.append("RU audio")

        tags_line = " • ".join(tags) if tags else "Цифровой релиз"
        date_line = f"📅 Digital release: {movie.digital_release_date or movie.first_detected_at[:10]}"

        lines = [
            f"🎬 <b>{movie.title}</b>{orig}{year_str}",
            "",
            rating_str,
        ]
        if pop_str:
            lines.append(pop_str)
        lines.extend([
            f"🎞 <code>{tags_line}</code>",
            date_line,
        ])

        if movie.overview:
            short_overview = movie.overview[:180] + "..." if len(movie.overview) > 180 else movie.overview
            lines.append(f"\n<i>{short_overview}</i>")

        return "\n".join(lines)

    def notify_new_releases(self, new_movies: List[Movie]) -> int:
        """Sends notifications for newly detected movies. Returns count sent."""
        if not self.enabled:
            logger.info("Telegram notification skipped: credentials not configured.")
            return 0

        sent_count = 0
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        # Limit to 10 per run to prevent flood limit
        for movie in new_movies[:10]:
            text = self.format_movie_message(movie)
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            }
            try:
                resp = requests.post(url, json=payload, timeout=8.0)
                if resp.status_code == 200:
                    sent_count += 1
                else:
                    logger.warning(f"Telegram API warning: {resp.status_code} - {resp.text}")
            except Exception as e:
                logger.error(f"Failed to send Telegram notification: {e}")

        return sent_count
