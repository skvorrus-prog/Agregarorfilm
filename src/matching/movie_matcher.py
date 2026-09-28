"""Movie matching and deduplication service."""
from typing import Optional, List, Dict
from src.models.movie import Movie
from src.normalizers.title_normalizer import normalize_title, title_similarity


class MovieMatcher:
    """Matches incoming releases to existing movies to prevent duplication."""

    def __init__(self, existing_movies: Optional[List[Movie]] = None):
        self.by_imdb: Dict[str, Movie] = {}
        self.by_tmdb: Dict[int, Movie] = {}
        self.movies_list: List[Movie] = []

        if existing_movies:
            for m in existing_movies:
                self.register(m)

    def register(self, movie: Movie) -> None:
        """Registers a movie into the matching indexes."""
        self.movies_list.append(movie)
        if movie.imdb_id:
            self.by_imdb[movie.imdb_id.strip()] = movie
        if movie.tmdb_id:
            self.by_tmdb[movie.tmdb_id] = movie

    def find_match(
        self,
        title: str,
        original_title: Optional[str] = None,
        year: Optional[int] = None,
        imdb_id: Optional[str] = None,
        tmdb_id: Optional[int] = None,
    ) -> Optional[Movie]:
        """
        Attempts to match candidate movie using multi-tiered strategy:
        1. Exact IMDb ID match
        2. Exact TMDB ID match
        3. Exact normalized title + matching year
        4. Fuzzy title matching (similarity >= 0.88) within +/- 1 year
        """
        # 1. IMDb ID
        if imdb_id and imdb_id.strip() in self.by_imdb:
            return self.by_imdb[imdb_id.strip()]

        # 2. TMDB ID
        if tmdb_id and tmdb_id in self.by_tmdb:
            return self.by_tmdb[tmdb_id]

        candidate_titles = [t for t in [title, original_title] if t]
        normalized_candidates = [normalize_title(t) for t in candidate_titles if t]

        if not normalized_candidates:
            return None

        # 3. Exact normalized title + matching year
        for movie in self.movies_list:
            movie_titles = [t for t in [movie.title, movie.original_title] if t]
            movie_normalized = [normalize_title(t) for t in movie_titles]

            # Compare titles
            title_matched = False
            for nc in normalized_candidates:
                if nc in movie_normalized:
                    title_matched = True
                    break

            if title_matched:
                if year is None or movie.year is None:
                    return movie
                if abs(movie.year - year) <= 1:
                    return movie

        # 4. Fuzzy title match (Levenshtein / SequenceMatcher >= 0.88)
        best_match: Optional[Movie] = None
        best_score = 0.0

        for movie in self.movies_list:
            # Check year compatibility
            if year and movie.year and abs(movie.year - year) > 1:
                continue

            movie_titles = [t for t in [movie.title, movie.original_title] if t]
            for c_title in candidate_titles:
                for m_title in movie_titles:
                    score = title_similarity(c_title, m_title)
                    if score >= 0.88 and score > best_score:
                        best_score = score
                        best_match = movie

        return best_match
