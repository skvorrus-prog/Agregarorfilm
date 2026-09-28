"""Unit tests for movie matching and deduplication service."""
from src.matching.movie_matcher import MovieMatcher
from src.models.movie import Movie


def test_match_by_imdb_id():
    m1 = Movie(id="tt15398776", title="Oppenheimer", year=2023, imdb_id="tt15398776")
    matcher = MovieMatcher([m1])

    matched = matcher.find_match(title="Some Different Title", imdb_id="tt15398776")
    assert matched is not None
    assert matched.id == "tt15398776"


def test_match_by_tmdb_id():
    m1 = Movie(id="m_123", title="Inside Out 2", year=2024, tmdb_id=1022789)
    matcher = MovieMatcher([m1])

    matched = matcher.find_match(title="Головоломка 2", tmdb_id=1022789)
    assert matched is not None
    assert matched.title == "Inside Out 2"


def test_match_by_normalized_title_and_year():
    m1 = Movie(id="tt6263850", title="Дэдпул и Росомаха", original_title="Deadpool & Wolverine", year=2024)
    matcher = MovieMatcher([m1])

    # Candidate with different punctuation
    matched = matcher.find_match(title="Deadpool and Wolverine", year=2024)
    assert matched is not None
    assert matched.id == "tt6263850"


def test_no_false_positive_for_different_movies():
    m1 = Movie(id="m_1", title="Dune: Part One", year=2021)
    matcher = MovieMatcher([m1])

    matched = matcher.find_match(title="Dune: Part Two", year=2024)
    assert matched is None
