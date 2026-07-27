# GPT Image MCP

FastAPI + MCP service for generating images with OpenAI `gpt-image-1` and serving them as public files.

## What it does

- Exposes an MCP tool for image generation.
- Saves generated images locally.
- Returns a public URL for each image.
- Provides simple HTTP health checks.

## Endpoints

- `GET /` - service status
- `GET /health` - HTTP health check
- `POST /mcp` - MCP transport
- `GET /images/{filename}` - served generated images

## Setup

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Fill in your values:

- `OPENAI_API_KEY` - required
- `PUBLIC_URL` - public base URL where this service is reachable
- `IMAGE_DIR` - image storage directory

For local runs without Docker, `IMAGE_DIR=data/images` is a good choice.
For Docker, keep it as `/data/images`.

## Run locally

Install dependencies and start the app:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Run with Docker

```bash
docker compose up --build
```

## Tests

Run the built-in tests with:

```bash
python3 -m unittest discover -s tests -p "test*.py" -v
```

## Publish to GitHub

If this folder is not a git repository yet, initialize it first:

```bash
git init
git add .
git commit -m "Initial commit"
```

Create a new empty repository on GitHub, then connect and push:

```bash
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

If you already have a git remote, use:

```bash
git remote -v
git push -u origin main
```

## Notes

- The service expects `OPENAI_API_KEY` to be set.
- `PUBLIC_URL` should point to the domain where the generated images will be reachable.
- Generated files are stored in `data/images` by default when running locally.
