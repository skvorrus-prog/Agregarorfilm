/**
 * Instant full-text search across titles and external IDs.
 */

export class SearchEngine {
  constructor(movies = []) {
    this.movies = movies;
  }

  setMovies(movies) {
    this.movies = movies;
  }

  search(query) {
    if (!query || !query.trim()) {
      return this.movies;
    }

    const clean = query.trim().toLowerCase();
    const tokens = clean.split(/\s+/);

    return this.movies.filter(m => {
      // Direct ID exact/prefix matches
      if (m.imdb_id && m.imdb_id.toLowerCase().includes(clean)) return true;
      if (m.tmdb_id && String(m.tmdb_id).includes(clean)) return true;

      const title = (m.title || "").toLowerCase();
      const origTitle = (m.original_title || "").toLowerCase();
      const combined = `${title} ${origTitle}`;

      // All tokens must match either title or original title
      return tokens.every(token => combined.includes(token));
    });
  }
}
