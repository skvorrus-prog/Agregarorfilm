"""Unit tests for collectors, date parsing, and resilience."""
from src.collectors.tmdb import TMDBDigitalSource
from src.collectors.release_rss import ReleaseRSSSource
from src.collectors.base import RawRelease
from src.models.enums import PipelineStatus


def test_tmdb_collector_without_key():
    source = TMDBDigitalSource(api_key="")
    res = source.fetch_releases()
    assert res.status == PipelineStatus.SUCCESS
    assert len(res.releases) == 0
    assert "not configured" in (res.error_message or "").lower()


def test_rss_date_parsing_to_iso():
    source = ReleaseRSSSource()
    rfc_date = "Mon, 28 Sep 2026 22:21:54 +0300"
    iso_date = source._parse_pubdate_to_iso(rfc_date)
    assert iso_date is not None
    assert "2026-09-28" in iso_date
    assert "+00:00" in iso_date or "Z" in iso_date

    # Malformed date returns None without exception
    assert source._parse_pubdate_to_iso("invalid date string") is None


def test_raw_release_model():
    raw = RawRelease(
        raw_title="Some.Movie.2024.1080p",
        source_name="Test",
        source_release_date="2024-09-28T12:00:00Z",
    )
    assert raw.raw_title == "Some.Movie.2024.1080p"
    assert raw.metadata == {}
