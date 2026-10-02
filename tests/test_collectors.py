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


def test_cinemeta_search_strict_title_matching(monkeypatch):
    from src.collectors.cinemeta import CinemetaSource
    source = CinemetaSource()

    # Mock _safe_request to return search results where metas[0] is unrelated
    class MockResp:
        def json(self):
            return {
                "metas": [
                    {"id": "tt9999999", "name": "Completely Unrelated Film", "year": "2026"},
                    {"id": "tt34584846", "name": "Man of War", "year": "2026"},
                ]
            }

    monkeypatch.setattr(source, "_safe_request", lambda url: MockResp())
    monkeypatch.setattr(source, "fetch_movie_detail", lambda imdb_id: None)

    # Search for Ferret-Man: should reject both and return None
    res_mismatch = source.search_movie("Ferret-Man", year=2026)
    assert res_mismatch is None

    # Search for Man of War: should match correctly
    res_match = source.search_movie("Man of War", year=2026)
    assert res_match is not None
    assert res_match["imdb_id"] == "tt34584846"

