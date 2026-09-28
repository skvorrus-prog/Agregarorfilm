# 🎬 Digital Movie Releases — Агрегатор цифровых релизов фильмов

> Полностью автономный MVP веб-сервиса, который автоматически отслеживает появление фильмов в цифровом качестве (WEB-DL, BluRay, 4K UHD, HDR, русская озвучка) и формирует постоянно пополняемую историческую базу релизов без необходимости постоянно работающего VPS или домашнего сервера.

[![Tests](https://github.com/your-username/digital-movie-releases/actions/workflows/tests.yml/badge.svg)](https://github.com/your-username/digital-movie-releases/actions/workflows/tests.yml)
[![Tracker & Deploy](https://github.com/your-username/digital-movie-releases/actions/workflows/tracker.yml/badge.svg)](https://github.com/your-username/digital-movie-releases/actions/workflows/tracker.yml)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Demo-success)](https://your-username.github.io/digital-movie-releases/)

---

## 💡 Главная идея

Пользователь открывает сайт и сразу видит, какие фильмы появились в цифровом качестве:
* **Сегодня**
* **Вчера**
* **За последние 7 дней**
* **За последние 30 дней**
* **В этот месяц / В этот год / В предыдущий год**
* **В этот день** (сравнение одинаковых календарных дат разных лет: 28 сентября 2026, 2025, 2024...)
* **Календарь релизов** (сетка дней с индикацией количества вышедших фильмов)
* **Статистика** (динамика 4K, HDR, WEB-DL, русской озвучки и средний рейтинг)

---

## 🏛 Архитектурные принципы

1. **100% Serverless & Free**: Вся инфраструктура работает через GitHub:
   - **GitHub Repository** — хранение базы (SQLite) и структурированной истории (`data/history/YYYY/MM/DD.json`);
   - **GitHub Actions** — автоматический запуск сборщиков 2 раза в сутки (06:00 и 18:00 UTC) по cron;
   - **GitHub Pages** — быстрый статический сайт (HTML5, современный CSS, легковесный JS);
   - **Внешние API** — официальный TMDB, открытый Cinemeta (IMDb), открытые RSS-фиды релизов.
2. **Адаптерная система источников** (`src/collectors/`): каждый источник реализован как независимый адаптер с собственным rate-limiting, таймаутами и экспоненциальным backoff.
3. **Разделение сущностей `Movie` и `ReleaseEvent`**: один фильм существует в базе ровно один раз, но обрастает хронологией событий (официальный digital-релиз -> появление WEB-DL 1080p -> появление 4K HDR -> добавление русской дорожки).
4. **Строгое разделение дат**:
   - `digital_release_date` — официальная дата премьеры (VOD / Streaming);
   - `first_detected_at` — дата и время (UTC), когда агрегатор впервые обнаружил релиз;
   - `source_release_date` — дата публикации во вторичном фиде сигналов.
5. **Абсолютная идемпотентность**: повторный запуск сборщика 1, 2 или 10 раз не создаёт дубликатов фильмов или событий (`new_movies: 0`, `new_events: 0`).
6. **Честные метрики (без искусственных формул)**:
   - Рейтинг IMDb и количество голосов хранятся отдельно: `⭐ IMDb 7.8 (124K votes)`.
   - Популярность хранится с явным указанием источника: `🔥 Популярность: 842.3 (TMDB)`.
   - Отсутствующие значения отображаются как `—` (не `0`) и при сортировке помещаются в конец.
7. **Legal & Compliance**: сервис является исключительно информационным каталогом метаданных. Не хранит видеофайлы, не содержит торрент-файлов и ссылок на нелегальное скачивание.

---

## 🚀 Быстрый старт локально

### 1. Клонирование и установка зависимостей

Требуется **Python 3.10+**.

```bash
git clone https://github.com/your-username/digital-movie-releases.git
cd digital-movie-releases

# Создание виртуального окружения (рекомендуется)
python -m venv .venv
# Активация:
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Настройка конфигурации (.env)

Скопируйте пример файла конфигурации:

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
# TMDB API Key (бесплатный ключ на https://www.themoviedb.org/settings/api)
TMDB_API_KEY=your_tmdb_api_key_here

# Опционально: Telegram-уведомления
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

LOG_LEVEL=INFO
```
> **Важно**: Сервис полноценно работает даже **без** `TMDB_API_KEY` благодаря адаптерам Cinemeta и ReleaseRSS! Если ключ не указан, TMDB источник корректно пропускается, а система собирает релизы из открытых каталогов.

### 3. Запуск сборщика (Collector Pipeline)

```bash
# Запуск полного сбора данных
python scripts/run_pipeline.py

# Сбор за определенный период (диапазон дат)
python scripts/run_pipeline.py --from 2026-09-01 --to 2026-09-28

# Использование конкретных источников (например, cinemeta и rss)
python scripts/run_pipeline.py --sources cinemeta,rss
```

### 4. Сборка статического сайта

```bash
python scripts/build_site.py
```
Команда генерирует:
- `website/data/catalog.json` (каталог для мгновенного поиска и фильтрации)
- `website/data/latest.json` (свежие релизы для быстрого первого экрана)
- `website/data/calendar.json` (индекс по дням для календаря)
- `website/data/on_this_day.json` (индекс для режима "В этот день")
- `website/data/stats.json` (аналитика)
- `website/movie/<id>.html` (статические pre-rendered страницы фильмов для SEO)
- `website/sitemap.xml` и `website/robots.txt`

### 5. Локальный просмотр сайта

Запустите любой локальный HTTP-сервер:

```bash
python -m http.server -d website 8000
```
Откройте в браузере: **http://localhost:8000**

---

## ⚙️ Настройка автоматизации в GitHub Actions

### 1. Подключение GitHub Secrets

В вашем GitHub репозитории перейдите в **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret Name | Описание | Обязательно |
| :--- | :--- | :--- |
| `TMDB_API_KEY` | Бесплатный API ключ TMDB v3 | Рекомендуется (для официальных digital дат) |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота (от @BotFather) | Опционально (для уведомлений) |
| `TELEGRAM_CHAT_ID` | ID чата или канала для уведомлений | Опционально |

### 2. Настройка прав для GitHub Pages

В репозитории перейдите в **Settings** → **Pages**:
* **Source**: `GitHub Actions`

Перейдите в **Settings** → **Actions** → **General** → **Workflow permissions**:
* Выберите: **Read and write permissions** (для сохранения истории в Git).

### 3. Расписание запусков

Workflow `.github/workflows/tracker.yml` настроен на запуск по cron:
```yaml
schedule:
  - cron: "0 6,18 * * *" # Дважды в сутки в 06:00 и 18:00 UTC
```
Также доступен ручной запуск через вкладку **Actions** → **Digital Releases Tracker & Deploy** → **Run workflow**.

---

## 🧪 Запуск тестов

Комплексный набор модульных и интеграционных тестов проверяет:
* Парсинг технических тэгов релизов (WEB-DL, BluRay, 2160p 4K, HDR, Atmos, RU audio);
* Нормализацию названий и трансляцию римских цифр;
* Алгоритм сопоставления фильмов (IMDb ID, TMDB ID, fuzzy Levenshtein);
* Сохранение первого обнаружения (`first_detected_at`);
* Многократный повторный запуск без дублирования (Idempotency);
* Расчёт агрегированной статистики;
* Устойчивость к сбоям API и сетевым ошибкам.

```bash
python -m pytest -v
```

---

## 📱 Возможности веб-интерфейса

- **Быстрые переключатели на главном экране**:
  - `[🆕 Новые]` — сортировка по времени обнаружения/выхода;
  - `[⭐ IMDb]` — сортировка по рейтингу IMDb;
  - `[🔥 Популярные]` — сортировка по популярности TMDB;
  - `[4K]` — мгновенная фильтрация релизов в 2160p.
- **Интерактивная панель фильтров**:
  - Диапазон дат / готовые периоды;
  - Жанры, годы выпуска;
  - Минимальный рейтинг IMDb (например, `≥ 7.0`);
  - Минимальное число голосов IMDb (например, `≥ 10 000`);
  - Чекбоксы: `Только 4K`, `Только HDR / Dolby Vision`, `Только с русской озвучкой (RU)`.
- **Мгновенный поиск**:
  - По русскому названию, оригинальному названию, коду IMDb (`tt...`) или номеру TMDB.
- **Интерактивный календарь** (`calendar.html`):
  - Помесячная сетка с отображением числа релизов на каждый день.
  - Клик по дню выводит карточки вышедших фильмов.
- **Аналитическая статистика** (`stats.html`):
  - Графики распределения по месяцам, качествам, разрешениям и популярным жанрам.
- **Всплывающее окно и отдельная страница фильма**:
  - Хронологический таймлайн событий появления фильма в цифре.

---

## 📂 Структура репозитория

```text
digital-movie-releases/
├── src/
│   ├── collectors/       # Адаптеры источников (TMDB, Cinemeta, RSS, Fixture)
│   ├── normalizers/      # Парсеры релизов и нормализаторы названий
│   ├── matching/         # Алгоритмы сопоставления и дедупликации
│   ├── models/           # Сущности Movie, ReleaseEvent, Enums
│   ├── storage/          # SQLite repository и генератор истории
│   ├── pipeline/         # Оркестратор пайплайна и Telegram-уведомления
│   ├── statistics/       # Аналитика и агрегации
│   └── config/           # Настройки путей и окружения
│
├── data/
│   ├── releases.db       # Локальная SQLite база данных
│   └── history/          # Дневные исторические архивы (YYYY/MM/DD.json)
│
├── website/              # Статический веб-сайт для GitHub Pages
│   ├── index.html        # Главная страница
│   ├── calendar.html     # Календарь
│   ├── stats.html        # Статистика
│   ├── css/style.css     # Адаптивные стили (Mobile-first, Dark theme)
│   ├── js/               # Клиентские модули (поиск, фильтры, календарь)
│   ├── movie/            # Pre-rendered страницы фильмов
│   ├── sitemap.xml       # SEO sitemap
│   └── robots.txt
│
├── tests/                # Набор модульных и интеграционных тестов
├── scripts/              # CLI скрипты (run_pipeline, build_site, backfill)
├── .github/workflows/    # CI/CD пайплайны GitHub Actions
├── README.md
├── ARCHITECTURE.md
├── DATA_SOURCES.md
├── DEVELOPMENT.md
├── DEPLOYMENT.md
└── pyproject.toml
```

---

## 📄 Лицензия

Распространяется под свободной лицензией MIT.
