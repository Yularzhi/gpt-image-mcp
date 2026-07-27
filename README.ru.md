# GPT Image MCP

Сервис FastAPI + MCP для генерации и редактирования изображений через OpenAI `gpt-image-1`.

## Что делает проект

- Предоставляет MCP-инструменты для генерации и редактирования изображений.
- Сохраняет изображения локально.
- Возвращает публичные URL на сохранённые файлы.
- Даёт простой HTTP health-check.

## MCP-инструменты

- `generate_image` - создать новое изображение по текстовому запросу
- `edit_image` - отредактировать одно или несколько изображений, с поддержкой необязательной маски

## HTTP endpoint'ы

- `GET /` - статус сервиса
- `GET /health` - HTTP health-check
- `POST /mcp` - MCP endpoint
- `GET /images/{filename}` - раздача сохранённых изображений

## Настройка

1. Скопируй пример переменных окружения:

```bash
cp .env.example .env
```

2. Заполни значения:

- `OPENAI_API_KEY` - обязательно
- `PUBLIC_URL` - публичный base URL, по которому будет доступен сервис
- `IMAGE_DIR` - каталог для хранения изображений

Для локального запуска без Docker удобно использовать `IMAGE_DIR=data/images`.
Для Docker лучше оставить `/data/images`.

## Запуск локально

Установи зависимости и запусти приложение:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Запуск через Docker

```bash
docker compose up --build
```

## Тесты

Запуск тестов:

```bash
python3 -m unittest discover -s tests -p "test*.py" -v
```

## Публикация в GitHub

Если папка ещё не является git-репозиторием:

```bash
git init
git add .
git commit -m "Initial commit"
```

Создай пустой репозиторий на GitHub, затем подключи его и отправь код:

```bash
git branch -M main
git remote add origin git@github.com:<your-username>/<your-repo>.git
git push -u origin main
```

Если remote уже существует:

```bash
git remote -v
git push -u origin main
```

## Примечания

- Для работы нужен `OPENAI_API_KEY`.
- `PUBLIC_URL` должен указывать на домен, по которому будут доступны изображения.
- По умолчанию при локальном запуске файлы сохраняются в `data/images`.
