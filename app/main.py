from __future__ import annotations

import asyncio
import secrets
import time
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

try:
    from fastmcp.utilities.lifespan import combine_lifespans
except ModuleNotFoundError:
    from contextlib import AsyncExitStack

    def combine_lifespans(*lifespans):
        @asynccontextmanager
        async def _combined(app):
            async with AsyncExitStack() as stack:
                for lifespan in lifespans:
                    await stack.enter_async_context(lifespan(app))
                yield

        return _combined

from app.cleanup import cleanup_loop
from app.config import settings
from app.logging import get_logger, setup_logging
from app.mcp_server import mcp

import app.tools

setup_logging(settings.LOG_LEVEL)

logger = get_logger("gpt-image-mcp")
mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    settings.require_openai_api_key()

    cleanup_task: asyncio.Task[None] | None = None
    if settings.IMAGE_RETENTION_DAYS > 0:
        cleanup_task = asyncio.create_task(
            cleanup_loop(
                settings.IMAGE_DIR,
                settings.IMAGE_RETENTION_DAYS,
                settings.CLEANUP_INTERVAL_SECONDS,
            )
        )

    try:
        yield
    finally:
        if cleanup_task is not None:
            cleanup_task.cancel()
            with suppress(asyncio.CancelledError):
                await cleanup_task


app = FastAPI(
    title="GPT Image MCP",
    version="1.0.0",
    lifespan=combine_lifespans(app_lifespan, mcp_app.lifespan),
)

app.mount(
    "/images",
    StaticFiles(directory=settings.IMAGE_DIR),
    name="images",
)

app.mount(
    "/mcp",
    mcp_app,
)


def _requires_auth(path: str) -> bool:
    return path.startswith("/mcp") or path.startswith("/images")


@app.middleware("http")
async def auth_and_request_logging(request: Request, call_next):
    start = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"

    if (
        settings.MCP_API_KEY
        and request.method != "OPTIONS"
        and _requires_auth(request.url.path)
    ):
        authorization = request.headers.get("authorization", "")
        expected = f"Bearer {settings.MCP_API_KEY}"
        if not secrets.compare_digest(authorization, expected):
            logger.warning(
                "request_unauthorized",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("user-agent", ""),
                },
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    logger.info(
        "http_request",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", ""),
        },
    )
    return response


@app.get("/")
async def root():
    return {
        "service": "GPT Image MCP",
        "status": "running",
    }


@app.get("/health")
async def http_health():
    return {
        "status": "ok",
    }
