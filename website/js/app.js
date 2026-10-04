/**
 * Main application script coordinating data fetching, UI state, rendering, and modals.
 */

import { filterMovies, sortMovies } from './filters.js';
import { SearchEngine } from './search.js';

class App {
  constructor() {
    this.movies = [];
    this.searchEngine = new SearchEngine();
    this.onThisDayData = {};

    this.state = {
      period: 'today',
      specific_date: null,
      sort: 'newest',
      search: '',
      quality: 'all',
      resolution: 'all',
      genre: 'all',
      year: 'all',
      min_imdb: 0,
      max_imdb: 10,
      min_votes: 0,
      four_k_only: false,
      hdr_only: false,
      ru_only: false,
      quick_toggle: 'newest', // 'newest', 'imdb', 'popular', '4k'
    };

    this.initElements();
    this.attachEvents();
    this.loadData();
  }

  initElements() {
    this.cardsContainer = document.getElementById('movies-grid');
    this.heroTitle = document.getElementById('hero-title');
    this.heroSubtitle = document.getElementById('hero-subtitle');
    this.heroCount = document.getElementById('hero-count');
    this.searchInput = document.getElementById('search-input');
    this.sortSelect = document.getElementById('sort-select');
    this.modalOverlay = document.getElementById('modal-overlay');
    this.modalContent = document.getElementById('modal-body');
    this.modalClose = document.getElementById('modal-close');

    // Filter controls
    this.qualityFilter = document.getElementById('filter-quality');
    this.genreFilter = document.getElementById('filter-genre');
    this.yearFilter = document.getElementById('filter-year');
    this.minImdbInput = document.getElementById('filter-min-imdb');
    this.minVotesInput = document.getElementById('filter-min-votes');
    this.fourKCheckbox = document.getElementById('filter-4k');
    this.hdrCheckbox = document.getElementById('filter-hdr');
    this.ruCheckbox = document.getElementById('filter-ru');
  }

  attachEvents() {
    // Search
    this.searchInput?.addEventListener('input', (e) => {
      this.state.search = e.target.value;
      this.render();
    });

    // Sort select
    this.sortSelect?.addEventListener('change', (e) => {
      this.state.sort = e.target.value;
      this.render();
    });

    // Period buttons
    document.querySelectorAll('.tab-btn[data-period]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn[data-period]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.state.period = btn.getAttribute('data-period');
        this.state.specific_date = null;
        this.render();
      });
    });

    // Quick toggles (Section 36)
    document.querySelectorAll('.quick-toggle-btn[data-quick]').forEach(btn => {
      btn.addEventListener('click', () => {
        const toggle = btn.getAttribute('data-quick');
        document.querySelectorAll('.quick-toggle-btn[data-quick]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        if (toggle === 'newest') {
          this.state.sort = 'newest';
          this.state.four_k_only = false;
        } else if (toggle === 'imdb') {
          this.state.sort = 'imdb_desc';
          this.state.four_k_only = false;
        } else if (toggle === 'popular') {
          this.state.sort = 'pop_desc';
          this.state.four_k_only = false;
        } else if (toggle === '4k') {
          this.state.four_k_only = true;
        }
        if (this.sortSelect) this.sortSelect.value = this.state.sort;
        if (this.fourKCheckbox) this.fourKCheckbox.checked = this.state.four_k_only;
        this.render();
      });
    });

    // Detailed filter inputs
    this.qualityFilter?.addEventListener('change', (e) => {
      this.state.quality = e.target.value;
      this.render();
    });

    this.genreFilter?.addEventListener('change', (e) => {
      this.state.genre = e.target.value;
      this.render();
    });

    this.yearFilter?.addEventListener('change', (e) => {
      this.state.year = e.target.value;
      this.render();
    });

    this.minImdbInput?.addEventListener('input', (e) => {
      this.state.min_imdb = parseFloat(e.target.value) || 0;
      this.render();
    });

    this.minVotesInput?.addEventListener('input', (e) => {
      this.state.min_votes = parseInt(e.target.value, 10) || 0;
      this.render();
    });

    this.fourKCheckbox?.addEventListener('change', (e) => {
      this.state.four_k_only = e.target.checked;
      this.render();
    });

    this.hdrCheckbox?.addEventListener('change', (e) => {
      this.state.hdr_only = e.target.checked;
      this.render();
    });

    this.ruCheckbox?.addEventListener('change', (e) => {
      this.state.ru_only = e.target.checked;
      this.render();
    });

    // Reset filters button
    document.getElementById('reset-filters-btn')?.addEventListener('click', () => {
      this.state.quality = 'all';
      this.state.genre = 'all';
      this.state.year = 'all';
      this.state.min_imdb = 0;
      this.state.min_votes = 0;
      this.state.four_k_only = false;
      this.state.hdr_only = false;
      this.state.ru_only = false;

      if (this.qualityFilter) this.qualityFilter.value = 'all';
      if (this.genreFilter) this.genreFilter.value = 'all';
      if (this.yearFilter) this.yearFilter.value = 'all';
      if (this.minImdbInput) this.minImdbInput.value = '';
      if (this.minVotesInput) this.minVotesInput.value = '';
      if (this.fourKCheckbox) this.fourKCheckbox.checked = false;
      if (this.hdrCheckbox) this.hdrCheckbox.checked = false;
      if (this.ruCheckbox) this.ruCheckbox.checked = false;

      this.render();
    });

    // Modal close
    this.modalClose?.addEventListener('click', () => this.closeModal());
    this.modalOverlay?.addEventListener('click', (e) => {
      if (e.target === this.modalOverlay) this.closeModal();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.closeModal();
    });

    // Floating Scroll-to-Top Button
    const scrollBtn = document.getElementById('scroll-top-btn');
    if (scrollBtn) {
      window.addEventListener('scroll', () => {
        if (window.scrollY > 280) {
          scrollBtn.classList.add('visible');
        } else {
          scrollBtn.classList.remove('visible');
        }
      }, { passive: true });
      scrollBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }
  }

  async loadData() {
    try {
      const resp = await fetch(`data/catalog.json?v=${Date.now()}`);
      if (!resp.ok) {
        throw new Error(`Catalog load failed: ${resp.status}`);
      }
      this.movies = await resp.json();
      this.searchEngine.setMovies(this.movies);
      this.populateFilterOptions();

      // Attempt to load on_this_day.json
      try {
        const otdResp = await fetch(`data/on_this_day.json?v=${Date.now()}`);
        if (otdResp.ok) {
          this.onThisDayData = await otdResp.json();
        }
      } catch (e) {
        console.warn('on_this_day.json not loaded', e);
      }

      this.render();
    } catch (err) {
      console.error('Error loading data:', err);
      if (this.cardsContainer) {
        this.cardsContainer.innerHTML = `
          <div class="col-span-full p-8 text-center text-gray-400">
            <p class="text-lg font-semibold text-white mb-2">Каталог обновляется</p>
            <p class="text-sm">Данные еще формируются. Запустите сборщик релизов.</p>
          </div>
        `;
      }
    }
  }

  populateFilterOptions() {
    const genres = new Set();
    const years = new Set();

    this.movies.forEach(m => {
      if (m.genres) m.genres.forEach(g => genres.add(g));
      if (m.year) years.add(m.year);
    });

    if (this.genreFilter) {
      const sortedGenres = Array.from(genres).sort();
      sortedGenres.forEach(g => {
        const opt = document.createElement('option');
        opt.value = g;
        opt.textContent = g;
        this.genreFilter.appendChild(opt);
      });
    }

    if (this.yearFilter) {
      const sortedYears = Array.from(years).sort((a, b) => b - a);
      sortedYears.forEach(y => {
        const opt = document.createElement('option');
        opt.value = y;
        opt.textContent = y;
        this.yearFilter.appendChild(opt);
      });
    }
  }

  getFilteredAndSortedMovies() {
    let pool = this.searchEngine.search(this.state.search);
    let filtered = filterMovies(pool, this.state);
    return sortMovies(filtered, this.state.sort);
  }

  updateHero(count) {
    const periodTitles = {
      today: 'Что вышло сегодня',
      yesterday: 'Что вышло вчера',
      last7: 'Релизы за последние 7 дней',
      last30: 'Релизы за последние 30 дней',
      this_month: 'Релизы за этот месяц',
      this_year: 'Релизы за этот год',
      prev_year: 'Релизы за предыдущий год',
      all: 'Полный каталог цифровых релизов',
      on_this_day: 'В этот день в разные годы',
    };

    const title = this.state.specific_date
      ? `Релизы за ${this.formatDate(this.state.specific_date)}`
      : (periodTitles[this.state.period] || 'Каталог цифровых релизов');

    if (this.heroTitle) this.heroTitle.textContent = title;

    const todayStr = new Date().toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
    if (this.heroSubtitle) this.heroSubtitle.textContent = todayStr;

    if (this.heroCount) {
      this.heroCount.textContent = `${count} ${this.formatMovieWord(count)}`;
    }
  }

  render() {
    if (!this.cardsContainer) return;

    if (this.state.period === 'on_this_day') {
      this.renderOnThisDay();
      return;
    }

    const items = this.getFilteredAndSortedMovies();
    this.updateHero(items.length);

    if (items.length === 0) {
      this.cardsContainer.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 4rem 1rem; text-align: center; color: var(--text-muted);">
          <p style="font-size: 1.25rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem;">Ничего не найдено</p>
          <p style="font-size: 0.9rem;">Попробуйте смягчить фильтры или изменить поисковый запрос.</p>
        </div>
      `;
      return;
    }

    const html = items.map(m => this.createCardHTML(m)).join('');
    this.cardsContainer.innerHTML = html;

    // Attach card click handlers
    this.cardsContainer.querySelectorAll('.movie-card[data-id]').forEach(card => {
      card.addEventListener('click', () => {
        const id = card.getAttribute('data-id');
        const movie = this.movies.find(x => x.id === id);
        if (movie) this.openModal(movie);
      });
    });
  }

  renderOnThisDay() {
    const now = new Date();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    const dayKey = `${mm}-${dd}`;
    const yearsMap = this.onThisDayData[dayKey] || {};

    let totalCount = 0;
    Object.values(yearsMap).forEach(list => totalCount += list.length);
    this.updateHero(totalCount);

    const sortedYears = Object.keys(yearsMap).sort((a, b) => b.localeCompare(a));

    if (sortedYears.length === 0) {
      this.cardsContainer.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 4rem 1rem; text-align: center; color: var(--text-muted);">
          <p style="font-size: 1.25rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem;">В этот день пока нет записей</p>
          <p style="font-size: 0.9rem;">История накапливается с каждым днем работы сервиса.</p>
        </div>
      `;
      return;
    }

    let html = '';
    sortedYears.forEach(year => {
      const yearMovies = yearsMap[year];
      html += `
        <div style="grid-column: 1 / -1; margin-top: 1.5rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.75rem;">
          <h2 style="font-size: 1.35rem; font-weight: 800; color: var(--accent);">${year} год</h2>
          <span class="hero-count-badge">${yearMovies.length}</span>
        </div>
      `;
      yearMovies.forEach(m => {
        html += this.createCardHTML(m);
      });
    });

    this.cardsContainer.innerHTML = html;

    this.cardsContainer.querySelectorAll('.movie-card[data-id]').forEach(card => {
      card.addEventListener('click', () => {
        const id = card.getAttribute('data-id');
        const movie = this.movies.find(x => x.id === id);
        if (movie) this.openModal(movie);
      });
    });
  }

  createCardHTML(m) {
    const ratingStr = (m.imdb_rating !== null && m.imdb_rating !== undefined)
      ? `⭐ ${m.imdb_rating.toFixed(1)}${m.imdb_vote_count ? ` <span class="badge-votes">(${this.formatVotes(m.imdb_vote_count)})</span>` : ''}`
      : '⭐ —';

    const popStr = m.popularity
      ? `<span class="badge-pop">🔥 ${Math.round(m.popularity)}</span>`
      : '';

    const posterUrl = m.poster || 'images/no-poster.svg';
    const releaseDate = m.digital_release_date || (m.first_detected_at ? m.first_detected_at.slice(0, 10) : '—');

    return `
      <div class="movie-card" data-id="${m.id}">
        <div class="poster-wrap">
          <img src="${posterUrl}" alt="${this.escapeHtml(m.title)}" loading="lazy" class="poster-img" onerror="this.src='images/no-poster.svg'">
          <div class="card-top-badges">
            <span class="badge-imdb">${ratingStr}</span>
            ${popStr}
          </div>
        </div>
        <div class="card-body">
          <h3 class="movie-title">${this.escapeHtml(m.title)}</h3>
          <p class="movie-orig-title">${this.escapeHtml(m.original_title || '')} ${m.year ? `(${m.year})` : ''}</p>

          <div class="specs-row">
            ${m.best_quality && m.best_quality !== 'unknown' ? `<span class="spec-badge spec-quality">${m.best_quality}</span>` : (m.digital_release_date ? `<span class="spec-badge spec-quality">Digital</span>` : '')}
            ${m.best_resolution && m.best_resolution !== 'unknown' ? `<span class="spec-badge spec-res">${m.best_resolution}</span>` : ''}
            ${m.has_4k ? `<span class="spec-badge spec-4k">4K</span>` : ''}
            ${m.has_hdr ? `<span class="spec-badge spec-hdr">HDR</span>` : ''}
            ${m.has_ru_audio ? `<span class="spec-badge spec-ru">RU</span>` : ''}
          </div>

          <div class="card-footer-date">Digital: ${this.formatDate(releaseDate)}</div>
        </div>
      </div>
    `;
  }

  openModal(movie) {
    if (!this.modalOverlay || !this.modalContent) return;

    const ratingVal = movie.imdb_rating !== null && movie.imdb_rating !== undefined ? movie.imdb_rating : '—';
    const popVal = movie.popularity ? `${movie.popularity.toFixed(1)} (${movie.popularity_source || 'TMDB'})` : '—';

    let timelineHTML = '';
    if (movie.events && movie.events.length > 0) {
      timelineHTML = movie.events.map(ev => {
        const dt = this.formatDate(ev.source_release_date || ev.detected_at);
        const eventTitle = this.formatEventType(ev.event_type);
        const tags = [ev.quality, ev.resolution, ev.hdr, ev.audio, ev.language].filter(x => x && x !== 'unknown');
        const tagsStr = tags.length > 0 ? tags.join(' • ') : (ev.source_name === 'TMDB' ? 'Цифровой релиз' : 'Обнаружен релиз');
        return `
          <div class="timeline-item">
            <span class="timeline-date">${dt}</span>
            <div>
              <div style="font-size: 0.85rem; font-weight: 700; color: #fff;">
                ${eventTitle}
                <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: normal;">(${ev.source_name})</span>
              </div>
              <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 0.2rem;">${tagsStr}</div>
              ${ev.release_group ? `<div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.2rem;">Релиз-группа: ${ev.release_group}</div>` : ''}
            </div>
          </div>
        `;
      }).join('');
    } else {
      timelineHTML = '<p style="font-size: 0.85rem; color: var(--text-muted);">События пока не зафиксированы.</p>';
    }

    this.modalContent.innerHTML = `
      <div class="modal-grid">
        <div>
          <img src="${movie.poster || 'images/no-poster.svg'}" alt="${this.escapeHtml(movie.title)}" style="width: 100%; border-radius: var(--radius-md); aspect-ratio: 2/3; object-fit: cover;" onerror="this.src='images/no-poster.svg'">
          <div style="margin-top: 0.85rem; display: flex; flex-direction: column; gap: 0.4rem;">
            <button id="trailer-toggle-btn" class="trailer-btn" type="button" style="width: 100%; justify-content: center;">
              <span class="play-icon">▶</span> <span id="trailer-btn-text">Смотреть трейлер</span>
            </button>
            ${movie.imdb_id ? `<a href="https://www.imdb.com/title/${movie.imdb_id}" target="_blank" rel="noopener" class="tab-btn" style="text-align: center; font-size: 0.8rem;">Открыть на IMDb ↗</a>` : ''}
            <a href="movie/${movie.id}.html" class="tab-btn" style="text-align: center; font-size: 0.8rem;">Страница фильма ↗</a>
          </div>
        </div>
        <div>
          <h2 style="font-size: 1.6rem; font-weight: 800; color: #fff; margin-bottom: 0.2rem;">${this.escapeHtml(movie.title)}</h2>
          <p style="font-size: 0.95rem; color: var(--text-muted); margin-bottom: 0.75rem;">
            ${this.escapeHtml(movie.original_title || '')} ${movie.year ? `(${movie.year})` : ''}
          </p>

          <div class="metrics-row" style="margin-bottom: 0.85rem; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <span class="badge-imdb" style="font-size: 0.85rem; padding: 0.2rem 0.55rem;">⭐ IMDb ${ratingVal}</span>
            ${movie.imdb_vote_count ? `<span style="font-size: 0.78rem; color: var(--text-muted);">👥 ${movie.imdb_vote_count.toLocaleString()}</span>` : ''}
            ${movie.popularity ? `<span class="badge-pop" style="font-size: 0.8rem; padding: 0.2rem 0.55rem;">🔥 Популярность: ${popVal}</span>` : ''}
          </div>

          <div class="specs-row" style="margin-bottom: 0.85rem; border: none; padding-top: 0;">
            ${movie.best_quality && movie.best_quality !== 'unknown' ? `<span class="spec-badge spec-quality">${movie.best_quality}</span>` : (movie.digital_release_date ? `<span class="spec-badge spec-quality">Digital</span>` : '')}
            ${movie.best_resolution && movie.best_resolution !== 'unknown' ? `<span class="spec-badge spec-res">${movie.best_resolution}</span>` : ''}
            ${movie.has_4k ? `<span class="spec-badge spec-4k">4K</span>` : ''}
            ${movie.has_hdr ? `<span class="spec-badge spec-hdr">HDR</span>` : ''}
            ${movie.has_ru_audio ? `<span class="spec-badge spec-ru">RU</span>` : ''}
          </div>

          <!-- Trailer Expandable Section -->
          <div id="trailer-section" class="trailer-section hidden">
            <div class="trailer-header">
              <div class="trailer-title">
                <span>🎬</span> Трейлер: <span>${this.escapeHtml(movie.title)}</span>
              </div>
              <div class="trailer-lang-group">
                <button id="trailer-ru-btn" type="button" class="trailer-lang-btn active">🇷🇺 Русский</button>
                <button id="trailer-en-btn" type="button" class="trailer-lang-btn">🇬🇧 English</button>
                <button id="trailer-close-inline-btn" type="button" class="trailer-lang-btn" style="margin-left: 0.35rem; color: #f87171;">✕ Свернуть</button>
              </div>
            </div>
            <div class="trailer-iframe-wrap">
              <iframe id="trailer-iframe" src="" title="Трейлер фильма" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
            </div>
            <div class="trailer-footer">
              <span>Трейлер загружается из открытых источников</span>
              <a id="trailer-direct-link" href="#" target="_blank" rel="noopener" class="trailer-yt-link">
                Открыть на YouTube ↗
              </a>
            </div>
          </div>

          <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6; margin-bottom: 1.25rem;">
            ${this.escapeHtml(movie.overview || 'Описание пока отсутствует.')}
          </p>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem; font-size: 0.82rem; border-top: 1px solid var(--border-subtle); padding-top: 0.85rem; margin-bottom: 1.25rem;">
            <div>
              <span style="color: var(--text-muted); display: block;">Жанры:</span>
              <span style="color: #fff;">${(movie.genres || []).join(', ') || '—'}</span>
            </div>
            <div>
              <span style="color: var(--text-muted); display: block;">Страны:</span>
              <span style="color: #fff;">${(movie.countries || []).join(', ') || '—'}</span>
            </div>
            <div>
              <span style="color: var(--text-muted); display: block;">Дата digital-релиза:</span>
              <span style="color: var(--accent); font-weight: 600;">${this.formatDate(movie.digital_release_date)}</span>
            </div>
            <div>
              <span style="color: var(--text-muted); display: block;">Впервые обнаружен:</span>
              <span style="color: #fff;">${this.formatDate(movie.first_detected_at ? movie.first_detected_at.slice(0, 10) : '')}</span>
            </div>
          </div>

          <h3 style="font-size: 1rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem;">🕒 Хронология релиза</h3>
          <div class="timeline">${timelineHTML}</div>
        </div>
      </div>
    `;

    // Trailer Controller
    const trailerBtn = this.modalContent.querySelector('#trailer-toggle-btn');
    const trailerSection = this.modalContent.querySelector('#trailer-section');
    const trailerIframe = this.modalContent.querySelector('#trailer-iframe');
    const trailerRuBtn = this.modalContent.querySelector('#trailer-ru-btn');
    const trailerEnBtn = this.modalContent.querySelector('#trailer-en-btn');
    const trailerCloseInlineBtn = this.modalContent.querySelector('#trailer-close-inline-btn');
    const trailerDirectLink = this.modalContent.querySelector('#trailer-direct-link');
    const trailerBtnText = this.modalContent.querySelector('#trailer-btn-text');

    let currentTrailerLang = 'ru';

    const getTrailerUrls = (lang) => {
      let q = '';
      if (lang === 'ru') {
        q = `${movie.title} русский трейлер ${movie.year || ''}`.trim();
      } else {
        const eng = movie.original_title || movie.title;
        q = `${eng} official trailer ${movie.year || ''}`.trim();
      }
      return {
        embed: `https://www.youtube-nocookie.com/embed?listType=search&list=${encodeURIComponent(q)}`,
        direct: `https://www.youtube.com/results?search_query=${encodeURIComponent(q)}`
      };
    };

    const updateTrailerView = (lang) => {
      currentTrailerLang = lang;
      if (trailerRuBtn && trailerEnBtn) {
        trailerRuBtn.classList.toggle('active', lang === 'ru');
        trailerEnBtn.classList.toggle('active', lang === 'en');
      }
      const urls = getTrailerUrls(lang);
      if (trailerIframe) trailerIframe.src = urls.embed;
      if (trailerDirectLink) trailerDirectLink.href = urls.direct;
    };

    const toggleTrailer = () => {
      if (!trailerSection) return;
      const isHidden = trailerSection.classList.contains('hidden');
      if (isHidden) {
        trailerSection.classList.remove('hidden');
        if (trailerBtn) trailerBtn.classList.add('active');
        if (trailerBtnText) trailerBtnText.textContent = 'Свернуть трейлер';
        updateTrailerView(currentTrailerLang);
      } else {
        trailerSection.classList.add('hidden');
        if (trailerBtn) trailerBtn.classList.remove('active');
        if (trailerBtnText) trailerBtnText.textContent = 'Смотреть трейлер';
        if (trailerIframe) trailerIframe.src = '';
      }
    };

    if (trailerBtn) trailerBtn.addEventListener('click', toggleTrailer);
    if (trailerCloseInlineBtn) trailerCloseInlineBtn.addEventListener('click', toggleTrailer);
    if (trailerRuBtn) trailerRuBtn.addEventListener('click', () => updateTrailerView('ru'));
    if (trailerEnBtn) trailerEnBtn.addEventListener('click', () => updateTrailerView('en'));

    this.modalOverlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  closeModal() {
    if (!this.modalOverlay) return;
    const iframe = this.modalContent ? this.modalContent.querySelector('#trailer-iframe') : null;
    if (iframe) iframe.src = '';
    this.modalOverlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  formatVotes(votes) {
    if (!votes) return '';
    if (votes >= 1000000) return `${(votes / 1000000).toFixed(1)}M votes`;
    if (votes >= 1000) return `${Math.round(votes / 1000)}K votes`;
    return `${votes} votes`;
  }

  formatDate(dateStr) {
    if (!dateStr || dateStr.length < 10) return '—';
    const parts = dateStr.slice(0, 10).split('-');
    if (parts.length !== 3) return dateStr;
    return `${parts[2]}.${parts[1]}.${parts[0]}`;
  }

  formatEventType(eventType) {
    if (!eventType) return 'Обнаружен релиз';
    const map = {
      'DIGITAL_PREMIERE': 'Цифровая премьера',
      'WEB_DL_DETECTED': 'Обнаружен WEB-DL',
      'BLURAY_DETECTED': 'Обнаружен BluRay',
      'RU_AUDIO_DETECTED': 'Русская озвучка',
      'UHD_DETECTED': 'Обнаружен 4K UHD',
      'RELEASE_DETECTED': 'Обнаружен релиз'
    };
    return map[eventType] || eventType.replace(/_/g, ' ');
  }

  formatMovieWord(c) {
    if (c % 10 === 1 && c % 100 !== 11) return 'фильм';
    if ([2, 3, 4].includes(c % 10) && ![12, 13, 14].includes(c % 100)) return 'фильма';
    return 'фильмов';
  }

  escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
});
