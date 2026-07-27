# GPT Image MCP

FastAPI + FastMCP service for generating and editing images with OpenAI image models.

## What you get

- MCP tools: `generate_image`, `edit_image`, `health`
- Streamable HTTP MCP transport at `POST /mcp/`
- HTTP health check at `GET /health`
- Static image hosting at `GET /images/{filename}`
- Optional bearer auth for MCP and image routes
- Upload validation, retry logic, structured logs, and image cleanup

## MCP tools

- `generate_image` creates a new image from text.
- `edit_image` edits one or more images and supports an optional mask.
- `health` returns a simple service status payload.

## Environment variables

Copy the example file first:

```bash
cp .env.example .env
```

Required:

- `OPENAI_API_KEY` - OpenAI API key

Optional:

- `PUBLIC_URL` - public base URL for returned image links
- `MCP_API_KEY` - bearer token required for `/mcp/` and `/images/*`
- `IMAGE_DIR` - image storage directory
- `LOG_LEVEL` - logging level, default `INFO`
- `MAX_UPLOAD_MB` - max size for uploaded images, default `50`
- `MAX_MASK_MB` - max size for masks, default `4`
- `MAX_IMAGE_EDGE_PX` - max image edge length, default `8192`
- `IMAGE_RETENTION_DAYS` - cleanup retention window, default `7`
- `CLEANUP_INTERVAL_SECONDS` - cleanup interval, default `86400`
- `OPENAI_RETRY_ATTEMPTS` - retry count for OpenAI image calls, default `3`
- `OPENAI_RETRY_BASE_DELAY_SECONDS` - retry backoff base, default `0.75`
- `REQUEST_TIMEOUT_SECONDS` - timeout for remote image downloads, default `60`

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

The MCP endpoint is available at:

- `http://localhost:8080/mcp/`

## Run with Docker

```bash
docker compose up --build
```

## Tests

```bash
python3 -m unittest discover -s tests -p "test*.py" -v
```

If you have `pytest` installed:

```bash
pytest -q
```

## Verify on GitHub

```bash
git remote -v
git push -u origin main
```

If you have not connected the repository yet:

```bash
git branch -M main
git remote add origin git@github.com:<your-username>/<your-repo>.git
git push -u origin main
```

## Notes

- `POST /mcp/` is the MCP transport endpoint expected by LobeHub.
- `generate_image` and `edit_image` return the same response shape.
- Returned image URLs use `PUBLIC_URL` when it is set, otherwise they fall back to `/images/{filename}`.
- Old images are cleaned up automatically according to `IMAGE_RETENTION_DAYS`.
