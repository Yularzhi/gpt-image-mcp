# GPT Image MCP

Сервис на FastAPI + FastMCP для генерации и редактирования изображений через OpenAI.

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/github/license/Yularzhi/gpt-image-mcp)](./LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/Yularzhi/gpt-image-mcp/ci.yml?branch=main)](./.github/workflows/ci.yml)

## Что есть в проекте

- MCP-инструменты: `generate_image`, `edit_image`, `health`
- MCP transport через Streamable HTTP на `POST /mcp/`
- HTTP health-check на `GET /health`
- Раздача изображений через `GET /images/{filename}`
- Необязательная bearer-авторизация для `/mcp/` и `/images/*`
- Валидация загрузок, retry, структурные логи и очистка старых файлов

## MCP-инструменты

- `generate_image` создаёт новое изображение по тексту.
- `edit_image` редактирует одно или несколько изображений и поддерживает необязательную маску.
- `health` возвращает простой статус сервиса.

## Переменные окружения

Сначала скопируй пример:

```bash
cp .env.example .env
```

Обязательно:

- `OPENAI_API_KEY` - ключ OpenAI

Опционально:

- `PUBLIC_URL` - публичный base URL для ссылок на изображения
- `MCP_API_KEY` - bearer-токен для `/mcp/` и `/images/*`
- `IMAGE_DIR` - каталог хранения изображений
- `LOG_LEVEL` - уровень логирования, по умолчанию `INFO`
- `MAX_UPLOAD_MB` - максимальный размер загружаемого изображения, по умолчанию `50`
- `MAX_MASK_MB` - максимальный размер маски, по умолчанию `4`
- `MAX_IMAGE_EDGE_PX` - максимальная длина стороны, по умолчанию `8192`
- `IMAGE_RETENTION_DAYS` - срок хранения файлов, по умолчанию `7`
- `CLEANUP_INTERVAL_SECONDS` - интервал очистки, по умолчанию `86400`
- `OPENAI_RETRY_ATTEMPTS` - число повторов запросов к OpenAI, по умолчанию `3`
- `OPENAI_RETRY_BASE_DELAY_SECONDS` - базовая задержка retry, по умолчанию `0.75`
- `REQUEST_TIMEOUT_SECONDS` - таймаут загрузки удалённых изображений, по умолчанию `60`

## Локальный запуск

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

MCP endpoint доступен по адресу:

- `http://localhost:8080/mcp/`

## Запуск через Docker

```bash
docker compose up --build
```

## Тесты

```bash
python3 -m unittest discover -s tests -p "test*.py" -v
```

Если установлен `pytest`:

```bash
pytest -q
```

## Публикация в GitHub

```bash
git remote -v
git push -u origin main
```

Если репозиторий ещё не подключён:

```bash
git branch -M main
git remote add origin git@github.com:<your-username>/<your-repo>.git
git push -u origin main
```

## Примечания

- `POST /mcp/` - это MCP endpoint, который ожидает LobeHub.
- `generate_image` и `edit_image` возвращают одинаковую структуру ответа.
- `edit_image` принимает файлы изображений только из `IMAGE_DIR` или публичные `http(s)` URL.
- Локальные пути вне `IMAGE_DIR` и private/localhost удалённые URL отклоняются из соображений безопасности.
- Если `PUBLIC_URL` задан, ссылки на изображения будут с ним; иначе будет использоваться `/images/{filename}`.
- Старые изображения автоматически удаляются по `IMAGE_RETENTION_DAYS`.

## Troubleshooting

- `401 Unauthorized`
  - Укажи `MCP_API_KEY` на сервере и передавай `Authorization: Bearer <token>` из клиента.
  - Если используется LobeHub или nginx, убедись, что прокси передаёт заголовок `Authorization`.
- `404 Not Found` на `/mcp/`
  - Используй адрес со слэшем в конце: `POST /mcp/`.
  - Проверь, что nginx проксирует запросы на локальный порт контейнера и не переписывает путь.
  - Убедись, что FastMCP подключён через `app.main:app`.
- `Invalid image` или `Unsupported image`
  - Используй настоящий PNG, JPEG или WEBP файл.
  - Для маски нужен только PNG, и её размер должен совпадать с первым входным изображением.
  - Проверь, что файл не повреждён и не превышает `MAX_UPLOAD_MB` или `MAX_MASK_MB`.
- `File not found` или `Remote image host`
  - Держи локальные пути внутри `IMAGE_DIR`.
  - Используй только публичные доступные `http(s)` URL.
- Ошибки OpenAI API
  - Проверь, что `OPENAI_API_KEY` задан и корректен.
  - Проверь лимиты, квоту и доступность модели.
  - Убедись, что у сервера есть исходящий доступ в OpenAI.
- Ссылка на изображение не открывается
  - Укажи `PUBLIC_URL` как внешний домен сервиса.
  - Проверь, что nginx раздаёт `/images/` и каталог изображений смонтирован в контейнер.
