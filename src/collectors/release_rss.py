"""Public RSS feed collector for secondary release signals."""
from datetime import datetime, timezone
import email.utils
from typing import Optional, List
import xml.etree.ElementTree as ET

from src.collectors.base import BaseSource, RawRelease, SourceResult
from src.models.enums import PipelineStatus
from src.normalizers.release_parser import ReleaseParser


class ReleaseRSSSource(BaseSource):
    """Collector tracking release feeds for quality, 4K, HDR, and audio signals."""

    DEFAULT_FEEDS = [
        "https://rutor.info/rss.php?category=1",
    ]

    def __init__(self, feed_urls: Optional[List[str]] = None):
        super().__init__(name="ReleaseRSS", rate_limit_delay=1.0, timeout=10.0, max_retries=2)
        self.feed_urls = feed_urls or self.DEFAULT_FEEDS

    def _parse_pubdate_to_iso(self, pub_date_str: Optional[str]) -> Optional[str]:
        """Converts RFC 2822 date to UTC ISO 8601 string."""
        if not pub_date_str:
            return None
        try:
            parsed_tuple = email.utils.parsedate_to_datetime(pub_date_str)
            utc_dt = parsed_tuple.astimezone(timezone.utc)
            return utc_dt.isoformat()
        except Exception:
            return None

    def fetch_releases(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> SourceResult:
        releases: List[RawRelease] = []
        errors = []

        for feed_url in self.feed_urls:
            try:
                resp = self._safe_request(feed_url)
                # Decode properly
                content = resp.content.decode("utf-8", errors="replace")
                root = ET.fromstring(content.encode("utf-8"))

                items = root.findall("./channel/item")
                for item in items:
                    title_elem = item.find("title")
                    pub_elem = item.find("pubDate")
                    if title_elem is None or not title_elem.text:
                        continue

                    raw_title = title_elem.text.strip()
                    pub_iso = self._parse_pubdate_to_iso(pub_elem.text if pub_elem is not None else None)

                    parsed = ReleaseParser.parse(raw_title)

                    raw_release = RawRelease(
                        raw_title=raw_title,
                        source_name=self.name,
                        source_release_date=pub_iso,
                        parsed_title=parsed.title,
                        parsed_original_title=parsed.original_title,
                        parsed_year=parsed.year,
                        metadata={
                            "quality": parsed.quality,
                            "resolution": parsed.resolution,
                            "hdr": parsed.hdr,
                            "audio": parsed.audio,
                            "language": parsed.language,
                            "release_group": parsed.release_group,
                            "is_secondary_signal": True,
                        }
                    )
                    releases.append(raw_release)

            except Exception as exc:
                errors.append(f"{feed_url}: {str(exc)}")

        if not releases and errors:
            return SourceResult(
                source_name=self.name,
                status=PipelineStatus.FAILED,
                releases=[],
                error_message="; ".join(errors),
                items_count=0,
            )

        status = PipelineStatus.PARTIAL_SUCCESS if errors else PipelineStatus.SUCCESS
        return SourceResult(
            source_name=self.name,
            status=status,
            releases=releases,
            error_message="; ".join(errors) if errors else None,
            items_count=len(releases),
        )
