from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


def remove_expired_images(directory: Path, retention_days: int) -> int:
    if retention_days <= 0:
        return 0

    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    removed = 0

    for path in directory.iterdir():
        if not path.is_file():
            continue

        try:
            modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        except FileNotFoundError:
            continue

        if modified_at < cutoff:
            with suppress(FileNotFoundError):
                path.unlink()
                removed += 1

    return removed


async def cleanup_loop(
    directory: Path,
    retention_days: int,
    interval_seconds: int,
) -> None:
    if retention_days <= 0:
        return

    while True:
        try:
            await asyncio.to_thread(remove_expired_images, directory, retention_days)
        except Exception:  # noqa: BLE001
            logger.exception(
                "cleanup_cycle_failed",
                extra={
                    "directory": str(directory),
                    "retention_days": retention_days,
                },
            )

        await asyncio.sleep(max(60, interval_seconds))
