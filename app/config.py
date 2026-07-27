from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return default if value is None else value.strip()


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if not raw:
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = _env(name)
    if not raw:
        return default
    return float(raw)


def _env_path(name: str, default: str) -> Path:
    raw = _env(name, default)
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


@dataclass(slots=True)
class Settings:
    OPENAI_API_KEY: str
    PUBLIC_URL: str = ""
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    IMAGE_DIR: Path = Path("data/images")
    LOG_LEVEL: str = "INFO"
    MCP_API_KEY: str = ""
    MAX_UPLOAD_MB: int = 50
    MAX_MASK_MB: int = 4
    MAX_IMAGE_EDGE_PX: int = 8192
    IMAGE_RETENTION_DAYS: int = 7
    CLEANUP_INTERVAL_SECONDS: int = 86_400
    OPENAI_RETRY_ATTEMPTS: int = 3
    OPENAI_RETRY_BASE_DELAY_SECONDS: float = 0.75
    REQUEST_TIMEOUT_SECONDS: float = 60.0

    def __post_init__(self) -> None:
        self.PUBLIC_URL = self.PUBLIC_URL.rstrip("/")
        self.LOG_LEVEL = self.LOG_LEVEL.upper()
        self.IMAGE_DIR = Path(self.IMAGE_DIR)
        self.IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    def require_openai_api_key(self) -> None:
        if not self.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is required. Set it in the environment before "
                "starting the service."
            )


settings = Settings(
    OPENAI_API_KEY=_env("OPENAI_API_KEY"),
    PUBLIC_URL=_env("PUBLIC_URL"),
    HOST=_env("HOST", "0.0.0.0"),
    PORT=_env_int("PORT", 8080),
    IMAGE_DIR=_env_path("IMAGE_DIR", "data/images"),
    LOG_LEVEL=_env("LOG_LEVEL", "INFO"),
    MCP_API_KEY=_env("MCP_API_KEY"),
    MAX_UPLOAD_MB=_env_int("MAX_UPLOAD_MB", 50),
    MAX_MASK_MB=_env_int("MAX_MASK_MB", 4),
    MAX_IMAGE_EDGE_PX=_env_int("MAX_IMAGE_EDGE_PX", 8192),
    IMAGE_RETENTION_DAYS=_env_int("IMAGE_RETENTION_DAYS", 7),
    CLEANUP_INTERVAL_SECONDS=_env_int("CLEANUP_INTERVAL_SECONDS", 86_400),
    OPENAI_RETRY_ATTEMPTS=_env_int("OPENAI_RETRY_ATTEMPTS", 3),
    OPENAI_RETRY_BASE_DELAY_SECONDS=_env_float(
        "OPENAI_RETRY_BASE_DELAY_SECONDS",
        0.75,
    ),
    REQUEST_TIMEOUT_SECONDS=_env_float("REQUEST_TIMEOUT_SECONDS", 60.0),
)
