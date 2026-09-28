"""Release event model representing a concrete detection or release occurrence."""
from datetime import datetime, timezone
import hashlib
from typing import Optional, Any
from pydantic import BaseModel, Field

from src.models.enums import QualityType, Resolution, EventType


class ReleaseEvent(BaseModel):
    id: str = Field(description="Deterministic unique ID for idempotency")
    movie_id: str = Field(description="ID of associated movie")
    event_type: str = Field(default=EventType.RELEASE_DETECTED.value)
    source_name: str = Field(description="Name of reporting source")
    source_release_date: Optional[str] = Field(default=None, description="ISO date from source feed")
    detected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO timestamp of initial detection"
    )
    quality: str = Field(default=QualityType.UNKNOWN.value)
    resolution: str = Field(default=Resolution.UNKNOWN.value)
    hdr: Optional[str] = Field(default=None, description="e.g. HDR, HDR10, Dolby Vision")
    audio: Optional[str] = Field(default=None, description="e.g. Atmos, 5.1, 7.1")
    language: Optional[str] = Field(default=None, description="e.g. RU, EN, MULTI")
    release_group: Optional[str] = Field(default=None)
    raw_title: Optional[str] = Field(default=None)
    details: Optional[dict[str, Any]] = Field(default=None)

    @classmethod
    def create(
        cls,
        movie_id: str,
        source_name: str,
        event_type: str = EventType.RELEASE_DETECTED.value,
        quality: str = QualityType.UNKNOWN.value,
        resolution: str = Resolution.UNKNOWN.value,
        hdr: Optional[str] = None,
        audio: Optional[str] = None,
        language: Optional[str] = None,
        release_group: Optional[str] = None,
        source_release_date: Optional[str] = None,
        detected_at: Optional[str] = None,
        raw_title: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> "ReleaseEvent":
        """Creates a ReleaseEvent with a deterministic unique ID."""
        key = (
            f"{movie_id}|{source_name}|{event_type}|{quality}|{resolution}|"
            f"{hdr or ''}|{audio or ''}|{language or ''}|{release_group or ''}|{source_release_date or ''}"
        )
        event_id = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        dt = detected_at or datetime.now(timezone.utc).isoformat()
        return cls(
            id=event_id,
            movie_id=movie_id,
            event_type=event_type,
            source_name=source_name,
            source_release_date=source_release_date,
            detected_at=dt,
            quality=quality,
            resolution=resolution,
            hdr=hdr,
            audio=audio,
            language=language,
            release_group=release_group,
            raw_title=raw_title,
            details=details,
        )
