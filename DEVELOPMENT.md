# Руководство для разработчиков (DEVELOPMENT.md)

## 1. Структура проекта

```text
src/
├── collectors/          # Адаптеры сбора данных
│   ├── base.py          # Базовый абстрактный класс BaseSource
│   ├── tmdb.py          # Адаптер официального TMDB API
│   ├── cinemeta.py      # Адаптер открытого каталога Cinemeta (IMDb)
│   ├── release_rss.py   # Адаптер открытых RSS/XML фидов
│   └── fixture.py       # Фикстурный адаптер для оффлайн-тестирования
├── normalizers/         # Парсинг и нормализация
│   ├── release_parser.py# Извлечение качества, 4K, HDR, звука, языка
│   └── title_normalizer.py # Нормализация строк и нечеткое сравнение
├── matching/            # Сопоставление фильмов (Deduplication)
│   └── movie_matcher.py # Многоуровневый матчер
├── models/              # Pydantic модели и Enums
│   ├── enums.py
│   ├── movie.py
│   └── release_event.py
├── storage/             # Хранилище
│   ├── db.py            # Инициализация SQLite схемы
│   ├── repository.py    # CRUD операции с базой
│   └── history_exporter.py # Генерация data/history/ и static JSON
├── pipeline/            # Оркестрация
│   ├── runner.py        # PipelineRunner
│   └── telegram.py      # Уведомления Telegram
├── statistics/          # Расчет аналитики
│   └── stats_generator.py
└── config/              # Конфигурация и пути
    └── settings.py
```

---

## 2. Разработка и добавление нового адаптера источника

Все источники наследуются от `BaseSource` (`src/collectors/base.py`):

```python
from src.collectors.base import BaseSource, RawRelease, SourceResult
from src.models.enums import PipelineStatus

class MyCustomSource(BaseSource):
    def __init__(self):
        super().__init__(
            name="MyCustomSource",
            rate_limit_delay=1.0,  # Задержка между запросами (сек)
            timeout=10.0,          # Таймаут на запрос (сек)
            max_retries=3          # Количество попыток с exponential backoff
        )

    def fetch_releases(self, date_from=None, date_to=None) -> SourceResult:
        releases = []
        try:
            # Вызов с автоматическим rate limiting и retry:
            resp = self._safe_request("https://api.example.com/releases")
            data = resp.json()

            for item in data:
                raw_rel = RawRelease(
                    raw_title=item["title"],
                    source_name=self.name,
                    source_release_date=item.get("pub_date"),
                    imdb_id=item.get("imdb_id"),
                    parsed_title=item.get("title"),
                    metadata={
                        "quality": item.get("quality"),
                        "resolution": item.get("resolution"),
                        "poster": item.get("poster")
                    }
                )
                releases.append(raw_rel)

            return SourceResult(
                source_name=self.name,
                status=PipelineStatus.SUCCESS,
                releases=releases,
                items_count=len(releases)
            )
        except Exception as e:
            return SourceResult(
                source_name=self.name,
                status=PipelineStatus.FAILED,
                releases=[],
                error_message=str(e),
                items_count=0
            )
```

Затем зарегистрируйте новый адаптер в `PipelineRunner` (`src/pipeline/runner.py`) или передайте через флаг `--sources`.

---

## 3. Запуск тестов

Тестовый набор написан на `pytest`:

```bash
# Запуск всех тестов с подробным выводом
python -m pytest -v

# Запуск только тестов идемпотентности
python -m pytest tests/test_pipeline_idempotency.py -v

# Запуск тестов нормализатора
python -m pytest tests/test_normalizer.py -v
```

---

## 4. Локальный запуск сценариев

### Тестовый прогон на фикстурах (без обращения к сети):
```bash
python scripts/run_pipeline.py --sources fixture --fixture tests/fixtures/sample_releases.json
```

### Сбор данных с реальных источников:
```bash
python scripts/run_pipeline.py
```

### Генерация статики сайта:
```bash
python scripts/build_site.py
```

### Исторический бэкфилл:
```bash
python scripts/backfill.py --from 2026-01-01 --to 2026-09-28
```
