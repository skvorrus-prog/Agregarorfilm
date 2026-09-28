# Руководство по развертыванию (DEPLOYMENT.md)

Полный процесс развертывания автономного сервиса в GitHub с нуля.

---

## Шаг 1: Создание репозитория на GitHub

1. Перейдите на [github.com/new](https://github.com/new).
2. Создайте новый публичный или приватный репозиторий (например, `digital-movie-releases`).
3. Инициализируйте локальный Git репозиторий и отправьте код:
   ```bash
   git init
   git add .
   git commit -m "feat: initial commit of digital movie releases aggregator"
   git branch -M main
   git remote add origin https://github.com/<ваш-username>/digital-movie-releases.git
   git push -u origin main
   ```

---

## Шаг 2: Настройка секретов (GitHub Secrets)

1. Откройте ваш репозиторий на GitHub.
2. Перейдите в **Settings** → **Secrets and variables** → **Actions**.
3. Нажмите кнопку **New repository secret**.
4. Добавьте:
   * **`TMDB_API_KEY`**: Ваш API ключ от [TheMovieDatabase](https://www.themoviedb.org/settings/api). *(Рекомендуется)*.
   * **`TELEGRAM_BOT_TOKEN`**: Токен вашего бота от [@BotFather](https://t.me/BotFather). *(Опционально)*.
   * **`TELEGRAM_CHAT_ID`**: ID вашего чата или канала. *(Опционально)*.

---

## Шаг 3: Настройка прав доступа для GitHub Actions

Для того чтобы workflow мог коммитить обновленную историю (`data/history/`) и базу (`data/releases.db`) обратно в репозиторий:

1. Перейдите в **Settings** → **Actions** → **General**.
2. Прокрутите до блока **Workflow permissions**.
3. Выберите: **Read and write permissions**.
4. Установите галочку: **Allow GitHub Actions to create and approve pull requests**.
5. Нажмите **Save**.

---

## Шаг 4: Настройка GitHub Pages

1. Перейдите в **Settings** → **Pages**.
2. В секции **Build and deployment**:
   * **Source**: выберите **GitHub Actions**.

---

## Шаг 5: Первый запуск и проверка

1. Перейдите на вкладку **Actions** в репозитории.
2. В левой колонке выберите workflow **Digital Releases Tracker & Deploy**.
3. Нажмите кнопку **Run workflow** справа.
4. Дождитесь завершения выполнения:
   - Шаг `Run Collector Pipeline` соберет релизы;
   - Шаг `Build Static Site and SEO Assets` сгенерирует файлы для Pages;
   - Шаг `Commit and Push Database & History` сохранит изменения данных;
   - Шаг `Deploy to GitHub Pages` опубликует сайт.
5. В сводке (Summary) workflow будет отображена подробная таблица результатов работы источников.
6. Откройте ссылку на GitHub Pages (обычно `https://<ваш-username>.github.io/digital-movie-releases/`).

---

## Шаг 6: Регламент работы в production

* Сборщик запускается автоматически каждые 12 часов (в 06:00 и 18:00 UTC).
* Если новых релизов не появилось, пустые коммиты не создаются (`No data changes detected. Skipping git commit.`).
* При сбое одного из вторичных источников остальные продолжают работу, формируя статус `PARTIAL_SUCCESS`.
