"""Application configuration and filesystem path definitions."""
import os
from pathlib import Path
from pydantic import BaseModel, Field

# Locate base directory relative to this file
SRC_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = SRC_DIR.parent


class Settings(BaseModel):
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "data"
    history_dir: Path = BASE_DIR / "data" / "history"
    website_dir: Path = BASE_DIR / "website"
    website_data_dir: Path = BASE_DIR / "website" / "data"
    database_path: Path = BASE_DIR / "data" / "releases.db"
    logs_dir: Path = BASE_DIR / "logs"

    tmdb_api_key: str = Field(default_factory=lambda: os.getenv("TMDB_API_KEY", "").strip())
    telegram_bot_token: str = Field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", "").strip())
    telegram_chat_id: str = Field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", "").strip())

    app_timezone: str = Field(default_factory=lambda: os.getenv("APP_TIMEZONE", "UTC").strip())
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").strip())

    def ensure_directories(self) -> None:
        """Creates necessary directory trees if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.website_dir.mkdir(parents=True, exist_ok=True)
        self.website_data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


config = Settings()
