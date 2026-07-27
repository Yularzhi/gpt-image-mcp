from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

T = TypeVar("T")


def _is_retryable_exception(exc: Exception) -> bool:
    module_name = exc.__class__.__module__.split(".", 1)[0]
    if module_name == "openai":
        return True

    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return True

    if isinstance(exc, httpx.HTTPError):
        return True

    return False


async def run_with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int,
    base_delay_seconds: float,
) -> T:
    attempts = max(1, attempts)
    base_delay_seconds = max(0.0, base_delay_seconds)

    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except Exception as exc:  # noqa: BLE001
            if not _is_retryable_exception(exc) or attempt == attempts:
                raise

            last_error = exc
            delay = base_delay_seconds * (2 ** (attempt - 1))
            delay += random.uniform(0.0, min(delay, 0.25))
            await asyncio.sleep(delay)

    if last_error is not None:
        raise last_error

    raise RuntimeError("Retry loop exited without a result")
