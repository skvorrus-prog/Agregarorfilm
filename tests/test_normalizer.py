"""Unit tests for release parser, title normalizer, and similarity logic."""
import pytest
from src.normalizers.release_parser import ReleaseParser
from src.normalizers.title_normalizer import normalize_title, title_similarity, extract_year


def test_parse_quality_types():
    assert ReleaseParser.parse_quality("Movie.2024.UHD.BluRay.2160p") == "UHD BluRay"
    assert ReleaseParser.parse_quality("Movie.2024.1080p.REMUX") == "REMUX"
    assert ReleaseParser.parse_quality("Movie.2024.1080p.BluRay.x264") == "BluRay"
    assert ReleaseParser.parse_quality("Movie.2024.WEB-DL.1080p") == "WEB-DL"
    assert ReleaseParser.parse_quality("Movie.2024.WEBRip.720p") == "WEBRip"
    assert ReleaseParser.parse_quality("Movie.2024.CamRip") == "unknown"


def test_parse_resolutions():
    assert ReleaseParser.parse_resolution("Movie.2024.2160p.WEB-DL") == "2160p"
    assert ReleaseParser.parse_resolution("Movie.2024.4K.UHD") == "2160p"
    assert ReleaseParser.parse_resolution("Movie.2024.1080p.x264") == "1080p"
    assert ReleaseParser.parse_resolution("Movie.2024.720p.WEB") == "720p"
    assert ReleaseParser.parse_resolution("Movie.2024.480p.DVDRip") == "480p"
    assert ReleaseParser.parse_resolution("Movie.2024.AVI") == "unknown"


def test_parse_hdr():
    assert ReleaseParser.parse_hdr("Movie.2024.2160p.DV.HDR10.x265") == "Dolby Vision / HDR10"
    assert ReleaseParser.parse_hdr("Movie.2024.2160p.Dolby.Vision") == "Dolby Vision"
    assert ReleaseParser.parse_hdr("Movie.2024.2160p.HDR10+") == "HDR10+"
    assert ReleaseParser.parse_hdr("Movie.2024.2160p.HDR10") == "HDR10"
    assert ReleaseParser.parse_hdr("Movie.2024.2160p.HDR") == "HDR"
    assert ReleaseParser.parse_hdr("Movie.2024.1080p.SDR") is None


def test_parse_audio():
    assert "Atmos" in ReleaseParser.parse_audio("Movie.2024.DDP5.1.Atmos")
    assert "5.1" in ReleaseParser.parse_audio("Movie.2024.DDP5.1.Atmos")
    assert "7.1" in ReleaseParser.parse_audio("Movie.2024.TrueHD.7.1")
    assert "DTS-HD" in ReleaseParser.parse_audio("Movie.2024.DTS-HD.MA.5.1")


def test_parse_language():
    assert ReleaseParser.parse_language("Movie.2024.WEB-DL.Dub") == "RU"
    assert ReleaseParser.parse_language("Movie.2024.WEB-DL.MVO") == "RU"
    assert ReleaseParser.parse_language("Фильм (2024) WEB-DLRip | Русский дубляж") == "RU"
    assert ReleaseParser.parse_language("Movie.2024.ENG") == "EN"
    assert ReleaseParser.parse_language("Movie.2024.MULTi") == "MULTI"


def test_parse_dual_language_title():
    raw = "Что мы скрываем / What We Hide (2025) WEB-DLRip"
    ru_t, orig_t, year = ReleaseParser.parse_title_and_year(raw)
    assert ru_t == "Что мы скрываем"
    assert orig_t == "What We Hide"
    assert year == 2025


def test_parse_scene_dot_title():
    raw = "Oppenheimer.2023.2160p.WEB-DL.DDP5.1.Atmos-FLUX"
    title, orig_t, year = ReleaseParser.parse_title_and_year(raw)
    assert title == "Oppenheimer"
    assert year == 2023


def test_title_normalizer():
    assert normalize_title("Deadpool & Wolverine") == "deadpool and wolverine"
    assert normalize_title("Gladiator II") == "gladiator 2"
    assert normalize_title("Fast & Furious 9: The Fast Saga") == "fast and furious 9 the fast saga"
    assert normalize_title("  Movie   Name...  ") == "movie name"


def test_title_similarity():
    sim = title_similarity("Dune: Part Two", "Dune Part 2")
    assert sim > 0.85

    diff = title_similarity("Oppenheimer", "Barbie")
    assert diff < 0.3


def test_extract_year():
    assert extract_year("Movie (2024)") == 2024
    assert extract_year("Movie.1999.1080p") == 1999
    assert extract_year("No year here") is None
