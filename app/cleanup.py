from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path


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

    await asyncio.to_thread(remove_expired_images, directory, retention_days)

    while True:
        await asyncio.sleep(max(60, interval_seconds))
        await asyncio.to_thread(remove_expired_images, directory, retention_days)
