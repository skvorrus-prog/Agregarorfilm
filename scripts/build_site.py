"""Static site generator creating static JSON, pre-rendered pages, sitemap, and robots.txt."""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.config.settings import config
from src.storage.repository import MovieRepository
from src.storage.history_exporter import HistoryExporter
from src.statistics.stats_generator import StatsGenerator


def generate_sitemap(movies, website_dir: Path, base_url: str = "https://digitalreleases.github.io") -> None:
    """Generates sitemap.xml for SEO indexing."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <url>',
        f'    <loc>{base_url}/</loc>',
        '    <changefreq>daily</changefreq>',
        '    <priority>1.0</priority>',
        '  </url>',
        '  <url>',
        f'    <loc>{base_url}/calendar.html</loc>',
        '    <changefreq>daily</changefreq>',
        '    <priority>0.8</priority>',
        '  </url>',
        '  <url>',
        f'    <loc>{base_url}/stats.html</loc>',
        '    <changefreq>daily</changefreq>',
        '    <priority>0.7</priority>',
        '  </url>',
    ]

    for m in movies:
        lastmod = m.last_updated_at[:10] if m.last_updated_at else datetime.now(timezone.utc).date().isoformat()
        lines.extend([
            '  <url>',
            f'    <loc>{base_url}/movie/{m.id}.html</loc>',
            f'    <lastmod>{lastmod}</lastmod>',
            '    <changefreq>weekly</changefreq>',
            '    <priority>0.6</priority>',
            '  </url>',
        ])

    lines.append('</urlset>')
    sitemap_file = website_dir / "sitemap.xml"
    with open(sitemap_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_robots(website_dir: Path, base_url: str = "https://digitalreleases.github.io") -> None:
    """Generates robots.txt."""
    content = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
    with open(website_dir / "robots.txt", "w", encoding="utf-8") as f:
        f.write(content)


def generate_individual_movie_pages(movies, website_dir: Path) -> None:
    """Creates static pre-rendered HTML pages for each movie for SEO and direct links."""
    movie_dir = website_dir / "movie"
    movie_dir.mkdir(parents=True, exist_ok=True)

    template_file = website_dir / "movie_template.html"
    if not template_file.exists():
        # Fallback template
        template_content = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{TITLE}} ({{YEAR}}) — Цифровой релиз фильма</title>
  <meta name="description" content="Дата цифрового релиза фильма {{TITLE}} ({{ORIGINAL_TITLE}}). Качество: {{QUALITY}}, разрешение: {{RESOLUTION}}.">
  <meta property="og:title" content="{{TITLE}} ({{YEAR}}) — Digital Release">
  <meta property="og:description" content="{{OVERVIEW}}">
  <meta property="og:image" content="{{POSTER}}">
  <link rel="stylesheet" href="../css/style.css">
</head>
<body class="bg-gray-900 text-white min-h-screen">
  <nav class="border-b border-gray-800 bg-gray-950/80 backdrop-blur sticky top-0 z-50">
    <div class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
      <a href="../index.html" class="flex items-center gap-2 text-xl font-bold text-indigo-400">
        <span>🎬</span> DIGITAL RELEASES
      </a>
      <div class="flex items-center gap-4 text-sm font-medium">
        <a href="../index.html" class="hover:text-indigo-400 transition">Каталог</a>
        <a href="../calendar.html" class="hover:text-indigo-400 transition">Календарь</a>
        <a href="../stats.html" class="hover:text-indigo-400 transition">Статистика</a>
      </div>
    </div>
  </nav>

  <main class="max-w-4xl mx-auto px-4 py-8">
    <a href="../index.html" class="text-sm text-gray-400 hover:text-white inline-flex items-center gap-1 mb-6">
      ← Вернуться в каталог
    </a>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 bg-gray-800/40 p-6 rounded-2xl border border-gray-700/50 shadow-xl">
      <div class="md:col-span-1">
        <img src="{{POSTER}}" alt="{{TITLE}}" class="w-full rounded-xl shadow-lg object-cover aspect-[2/3] bg-gray-800" onerror="this.src='../images/no-poster.svg'">
      </div>
      <div class="md:col-span-2 flex flex-col justify-between">
        <div>
          <h1 class="text-3xl font-extrabold text-white mb-1">{{TITLE}}</h1>
          <p class="text-lg text-gray-400 mb-4">{{ORIGINAL_TITLE}} <span class="text-gray-500">({{YEAR}})</span></p>

          <div class="flex flex-wrap items-center gap-3 mb-6">
            <span class="bg-amber-500/20 text-amber-300 border border-amber-500/30 px-3 py-1 rounded-lg text-sm font-semibold flex items-center gap-1">
              ⭐ IMDb {{IMDB_RATING}}
            </span>
            <span class="text-sm text-gray-400">👥 {{IMDB_VOTES}}</span>
            {{POPULARITY_BADGE}}
          </div>

          <div class="flex flex-wrap gap-2 mb-6">
            <span class="px-2.5 py-1 bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-md text-xs font-bold">{{QUALITY}}</span>
            <span class="px-2.5 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-md text-xs font-bold">{{RESOLUTION}}</span>
            {{HDR_BADGE}}
            {{RU_BADGE}}
          </div>

          <p class="text-gray-300 leading-relaxed text-sm mb-6">{{OVERVIEW}}</p>

          <div class="grid grid-cols-2 gap-4 text-sm border-t border-gray-700/50 pt-4">
            <div>
              <span class="text-gray-400 block text-xs">Жанры</span>
              <span class="font-medium text-gray-200">{{GENRES}}</span>
            </div>
            <div>
              <span class="text-gray-400 block text-xs">Страны</span>
              <span class="font-medium text-gray-200">{{COUNTRIES}}</span>
            </div>
            <div>
              <span class="text-gray-400 block text-xs">Официальный Digital Release</span>
              <span class="font-semibold text-indigo-400">{{DIGITAL_RELEASE_DATE}}</span>
            </div>
            <div>
              <span class="text-gray-400 block text-xs">Впервые обнаружен</span>
              <span class="font-medium text-gray-300">{{FIRST_DETECTED}}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <section class="mt-8 bg-gray-800/30 p-6 rounded-2xl border border-gray-700/40">
      <h2 class="text-xl font-bold mb-4 flex items-center gap-2">
        <span>🕒</span> Хронология и история релизов
      </h2>
      <div class="space-y-4">
        {{EVENTS_TIMELINE}}
      </div>
    </section>
  </main>

  <footer class="mt-16 border-t border-gray-800 py-8 text-center text-sm text-gray-500">
    Digital Movie Releases Tracker — Автоматический информационный сервис
  </footer>
</body>
</html>"""
    else:
        with open(template_file, "r", encoding="utf-8") as tf:
            template_content = tf.read()

    for m in movies:
        html = template_content
        html = html.replace("{{TITLE}}", m.title or "Без названия")
        html = html.replace("{{ORIGINAL_TITLE}}", m.original_title or "")
        html = html.replace("{{YEAR}}", str(m.year or ""))
        html = html.replace("{{OVERVIEW}}", m.overview or "Описание пока отсутствует.")
        html = html.replace("{{POSTER}}", m.poster or "../images/no-poster.svg")
        html = html.replace("{{QUALITY}}", m.best_quality or "unknown")
        html = html.replace("{{RESOLUTION}}", m.best_resolution or "unknown")
        html = html.replace("{{IMDB_RATING}}", f"{m.imdb_rating}" if m.imdb_rating is not None else "—")
        html = html.replace("{{IMDB_VOTES}}", f"{m.imdb_vote_count:,} голосов" if m.imdb_vote_count else "нет оценок")

        pop_badge = ""
        if m.popularity:
            src = m.popularity_source or "TMDB"
            pop_badge = f'<span class="bg-red-500/20 text-red-300 border border-red-500/30 px-3 py-1 rounded-lg text-sm font-semibold">🔥 Популярность: {m.popularity:.1f} ({src})</span>'
        html = html.replace("{{POPULARITY_BADGE}}", pop_badge)

        hdr_badge = '<span class="px-2.5 py-1 bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded-md text-xs font-bold">HDR</span>' if m.has_hdr else ''
        ru_badge = '<span class="px-2.5 py-1 bg-blue-500/20 text-blue-300 border border-blue-500/30 rounded-md text-xs font-bold">RU</span>' if m.has_ru_audio else ''
        html = html.replace("{{HDR_BADGE}}", hdr_badge)
        html = html.replace("{{RU_BADGE}}", ru_badge)

        html = html.replace("{{GENRES}}", ", ".join(m.genres) if m.genres else "—")
        html = html.replace("{{COUNTRIES}}", ", ".join(m.countries) if m.countries else "—")
        html = html.replace("{{DIGITAL_RELEASE_DATE}}", m.digital_release_date or "Не объявлена")
        html = html.replace("{{FIRST_DETECTED}}", m.first_detected_at[:10] if m.first_detected_at else "—")

        timeline_items = []
        if m.events:
            for ev in m.events:
                date_label = ev.source_release_date or ev.detected_at[:10]
                timeline_items.append(f"""
                <div class="flex items-start gap-4 p-3 bg-gray-900/60 rounded-xl border border-gray-700/30">
                  <div class="text-xs font-mono text-indigo-400 bg-indigo-950/60 px-2 py-1 rounded">{date_label}</div>
                  <div class="flex-1">
                    <div class="text-sm font-semibold text-white">{ev.event_type.replace('_', ' ')} <span class="text-xs text-gray-400 font-normal">({ev.source_name})</span></div>
                    <div class="text-xs text-gray-300 mt-1">{ev.quality} • {ev.resolution} {('• ' + ev.hdr) if ev.hdr else ''} {('• ' + ev.audio) if ev.audio else ''} {('• ' + ev.language) if ev.language else ''}</div>
                  </div>
                </div>""")
        else:
            timeline_items.append('<p class="text-sm text-gray-500">События пока не зафиксированы.</p>')

        html = html.replace("{{EVENTS_TIMELINE}}", "\n".join(timeline_items))

        out_path = movie_dir / f"{m.id}.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)


def main():
    print("Building static website assets...")
    repo = MovieRepository(config.database_path)
    movies = repo.get_all_movies(load_events=True)
    print(f"Loaded {len(movies)} movies from database.")

    stats = StatsGenerator.generate(movies)
    exporter = HistoryExporter(config)
    exporter.export_all(movies, stats)

    website_dir = config.website_dir
    website_dir.mkdir(parents=True, exist_ok=True)

    generate_individual_movie_pages(movies, website_dir)
    generate_sitemap(movies, website_dir)
    generate_robots(website_dir)

    print("Site build completed successfully!")


if __name__ == "__main__":
    main()
