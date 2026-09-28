"""Movie domain entity representing a film with release history and metrics."""
from datetime import datetime, timezone
import hashlib
from typing import Optional, List
from pydantic import BaseModel, Field

from src.models.enums import ReleaseStatus, QualityType, Resolution
from src.models.release_event import ReleaseEvent


RESOLUTION_RANK = {
    Resolution.RES_2160P.value: 4,
    "2160p": 4,
    "4K": 4,
    Resolution.RES_1080P.value: 3,
    "1080p": 3,
    Resolution.RES_720P.value: 2,
    "720p": 2,
    Resolution.RES_480P.value: 1,
    "480p": 1,
    Resolution.UNKNOWN.value: 0,
    "unknown": 0,
}

QUALITY_RANK = {
    QualityType.UHD_BLURAY.value: 5,
    QualityType.REMUX.value: 4,
    QualityType.BLURAY.value: 3,
    QualityType.WEB_DL.value: 2,
    QualityType.WEB_RIP.value: 1,
    QualityType.UNKNOWN.value: 0,
    "unknown": 0,
}


class Movie(BaseModel):
    id: str = Field(description="Stable unique ID, e.g. tt1234567 or generated m_<hash>")
    title: str = Field(description="Primary display title")
    original_title: Optional[str] = Field(default=None)
    year: Optional[int] = Field(default=None)
    overview: Optional[str] = Field(default=None)
    poster: Optional[str] = Field(default=None)
    backdrop: Optional[str] = Field(default=None)
    genres: List[str] = Field(default_factory=list)
    countries: List[str] = Field(default_factory=list)
    runtime: Optional[int] = Field(default=None, description="Runtime in minutes")

    # IDs
    imdb_id: Optional[str] = Field(default=None)
    tmdb_id: Optional[int] = Field(default=None)

    # Ratings & Votes
    imdb_rating: Optional[float] = Field(default=None)
    imdb_vote_count: Optional[int] = Field(default=None)
    tmdb_rating: Optional[float] = Field(default=None)
    tmdb_vote_count: Optional[int] = Field(default=None)

    # Popularity
    popularity: Optional[float] = Field(default=None)
    popularity_source: Optional[str] = Field(default=None, description="e.g. TMDB")

    # Release Dates
    theatrical_release_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    digital_release_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")

    # Timestamps
    first_detected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO timestamp of first detection"
    )
    last_updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO timestamp of latest modification"
    )

    # Status & aggregates
    status: str = Field(default=ReleaseStatus.ANNOUNCED.value)
    best_quality: str = Field(default=QualityType.UNKNOWN.value)
    best_resolution: str = Field(default=Resolution.UNKNOWN.value)
    has_4k: bool = Field(default=False)
    has_hdr: bool = Field(default=False)
    has_ru_audio: bool = Field(default=False)

    # Events timeline
    events: List[ReleaseEvent] = Field(default_factory=list)

    @classmethod
    def generate_id(cls, imdb_id: Optional[str] = None, tmdb_id: Optional[int] = None, title: str = "", year: Optional[int] = None) -> str:
        """Returns stable ID favoring imdb_id, then tmdb_id, then hash of title+year."""
        if imdb_id and imdb_id.startswith("tt"):
            return imdb_id.strip()
        if tmdb_id:
            return f"tmdb_{tmdb_id}"
        normalized = f"{title.lower().strip()}_{year or 0}"
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
        return f"m_{digest}"

    def add_event(self, event: ReleaseEvent) -> bool:
        """Adds release event if not already present (idempotent), updates aggregate flags."""
        for existing in self.events:
            if existing.id == event.id:
                return False  # Already present, no duplicate

        self.events.append(event)
        self.recompute_aggregates()
        self.last_updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def recompute_aggregates(self) -> None:
        """Recalculates best_quality, best_resolution, 4k, hdr, ru_audio and status based on events."""
        current_res_rank = RESOLUTION_RANK.get(self.best_resolution, 0)
        current_qual_rank = QUALITY_RANK.get(self.best_quality, 0)

        for ev in self.events:
            # Check 4K
            if ev.resolution in ("2160p", Resolution.RES_2160P.value) or (ev.raw_title and "2160p" in ev.raw_title.lower()):
                self.has_4k = True
            # Check HDR
            if ev.hdr or (ev.raw_title and any(h in ev.raw_title.upper() for h in ["HDR", "DOLBY VISION", "DV."])):
                self.has_hdr = True
            # Check Russian audio
            if ev.language == "RU" or (ev.raw_title and any(r in ev.raw_title.upper() for r in ["DUB", "MVO", "LVO", "RUS", "РУССКИЙ"])):
                self.has_ru_audio = True

            # Resolution comparison
            ev_res_rank = RESOLUTION_RANK.get(ev.resolution, 0)
            if ev_res_rank > current_res_rank:
                self.best_resolution = ev.resolution
                current_res_rank = ev_res_rank

            # Quality comparison
            ev_qual_rank = QUALITY_RANK.get(ev.quality, 0)
            if ev_qual_rank > current_qual_rank:
                self.best_quality = ev.quality
                current_qual_rank = ev_qual_rank

        # Status computation
        if self.has_4k or self.best_resolution == "2160p":
            self.status = ReleaseStatus.UHD_RELEASE.value
        elif self.best_quality in (QualityType.BLURAY.value, QualityType.REMUX.value, QualityType.UHD_BLURAY.value):
            self.status = ReleaseStatus.BLURAY_RELEASE.value
        elif self.best_quality in (QualityType.WEB_DL.value, QualityType.WEB_RIP.value):
            self.status = ReleaseStatus.WEB_RELEASE.value
        elif self.digital_release_date:
            self.status = ReleaseStatus.DIGITAL_RELEASE.value
        elif not self.status:
            self.status = ReleaseStatus.ANNOUNCED.value
