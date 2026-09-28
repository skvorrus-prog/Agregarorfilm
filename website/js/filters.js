/**
 * Filter and sorting engine for movie catalog.
 */

export function filterMovies(movies, criteria) {
  const now = new Date();
  const todayStr = now.toISOString().slice(0, 10);

  // Compute reference dates
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  const yesterdayStr = yesterday.toISOString().slice(0, 10);

  const d7 = new Date(now);
  d7.setDate(d7.getDate() - 7);
  const d7Str = d7.toISOString().slice(0, 10);

  const d30 = new Date(now);
  d30.setDate(d30.getDate() - 30);
  const d30Str = d30.toISOString().slice(0, 10);

  const currentYear = now.getFullYear();
  const currentMonthStr = todayStr.slice(0, 7);

  return movies.filter(m => {
    const movieDate = m.digital_release_date || (m.first_detected_at ? m.first_detected_at.slice(0, 10) : "");

    // 1. Period filter
    if (criteria.period === "today") {
      if (movieDate !== todayStr) return false;
    } else if (criteria.period === "yesterday") {
      if (movieDate !== yesterdayStr) return false;
    } else if (criteria.period === "last7") {
      if (movieDate < d7Str) return false;
    } else if (criteria.period === "last30") {
      if (movieDate < d30Str) return false;
    } else if (criteria.period === "this_month") {
      if (!movieDate.startsWith(currentMonthStr)) return false;
    } else if (criteria.period === "this_year") {
      if (m.year !== currentYear && !movieDate.startsWith(String(currentYear))) return false;
    } else if (criteria.period === "prev_year") {
      const prevY = currentYear - 1;
      if (m.year !== prevY && !movieDate.startsWith(String(prevY))) return false;
    } else if (criteria.specific_date) {
      if (movieDate !== criteria.specific_date) return false;
    }

    // 2. 4K
    if (criteria.four_k_only && !m.has_4k && m.best_resolution !== "2160p") {
      return false;
    }

    // 3. HDR
    if (criteria.hdr_only && !m.has_hdr) {
      return false;
    }

    // 4. RU Audio
    if (criteria.ru_only && !m.has_ru_audio) {
      return false;
    }

    // 5. Quality
    if (criteria.quality && criteria.quality !== "all") {
      if (m.best_quality !== criteria.quality) return false;
    }

    // 6. Resolution
    if (criteria.resolution && criteria.resolution !== "all") {
      if (m.best_resolution !== criteria.resolution) return false;
    }

    // 7. Genre
    if (criteria.genre && criteria.genre !== "all") {
      if (!m.genres || !m.genres.includes(criteria.genre)) return false;
    }

    // 8. Year
    if (criteria.year && criteria.year !== "all") {
      if (String(m.year) !== String(criteria.year)) return false;
    }

    // 9. IMDb Rating minimum
    if (criteria.min_imdb !== undefined && criteria.min_imdb !== null && criteria.min_imdb > 0) {
      if (m.imdb_rating === null || m.imdb_rating === undefined || m.imdb_rating < criteria.min_imdb) {
        return false;
      }
    }

    // 10. IMDb Rating maximum
    if (criteria.max_imdb !== undefined && criteria.max_imdb !== null && criteria.max_imdb < 10) {
      if (m.imdb_rating === null || m.imdb_rating === undefined || m.imdb_rating > criteria.max_imdb) {
        return false;
      }
    }

    // 11. Min Votes
    if (criteria.min_votes && criteria.min_votes > 0) {
      if (!m.imdb_vote_count || m.imdb_vote_count < criteria.min_votes) {
        return false;
      }
    }

    return true;
  });
}

export function sortMovies(movies, sortKey) {
  const items = [...movies];

  return items.sort((a, b) => {
    switch (sortKey) {
      case "newest":
      default: {
        const da = a.digital_release_date || a.first_detected_at || "";
        const db = b.digital_release_date || b.first_detected_at || "";
        return db.localeCompare(da);
      }
      case "imdb_desc": {
        if (a.imdb_rating === null || a.imdb_rating === undefined) return 1;
        if (b.imdb_rating === null || b.imdb_rating === undefined) return -1;
        return b.imdb_rating - a.imdb_rating;
      }
      case "imdb_asc": {
        if (a.imdb_rating === null || a.imdb_rating === undefined) return 1;
        if (b.imdb_rating === null || b.imdb_rating === undefined) return -1;
        return a.imdb_rating - b.imdb_rating;
      }
      case "pop_desc": {
        if (a.popularity === null || a.popularity === undefined) return 1;
        if (b.popularity === null || b.popularity === undefined) return -1;
        return b.popularity - a.popularity;
      }
      case "pop_asc": {
        if (a.popularity === null || a.popularity === undefined) return 1;
        if (b.popularity === null || b.popularity === undefined) return -1;
        return a.popularity - b.popularity;
      }
      case "votes_desc": {
        const va = a.imdb_vote_count || 0;
        const vb = b.imdb_vote_count || 0;
        if (!va && !vb) return 0;
        if (!va) return 1;
        if (!vb) return -1;
        return vb - va;
      }
      case "digital_date": {
        const da = a.digital_release_date || "";
        const db = b.digital_release_date || "";
        if (!da && !db) return 0;
        if (!da) return 1;
        if (!db) return -1;
        return db.localeCompare(da);
      }
      case "detected_date": {
        const da = a.first_detected_at || "";
        const db = b.first_detected_at || "";
        return db.localeCompare(da);
      }
    }
  });
}
