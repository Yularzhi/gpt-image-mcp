from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.logging import setup_logging
from app.mcp_server import mcp

import app.tools

setup_logging(settings.LOG_LEVEL)

mcp_app = mcp.http_app(path="/")

app = FastAPI(
    title="GPT Image MCP",
    version="1.0.0",
    lifespan=mcp_app.lifespan,
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
