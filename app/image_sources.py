from __future__ import annotations

import ipaddress
import socket
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import httpx

from app.config import settings


def _within_directory(path: Path, root: Path) -> bool:
    resolved_path = path.resolve(strict=False)
    resolved_root = root.resolve(strict=False)
    return resolved_path == resolved_root or resolved_path.is_relative_to(resolved_root)


def _safe_local_candidate(candidate: Path) -> Path | None:
    if not candidate.exists():
        return None

    if not _within_directory(candidate, settings.IMAGE_DIR):
        return None

    return candidate.resolve(strict=False)


def resolve_local_image_source(source: str) -> Path | None:
    public_url = settings.PUBLIC_URL

    if public_url:
        public_prefix = f"{public_url}/images/"
        if source.startswith(public_prefix):
            relative_path = source.removeprefix(public_prefix)
            candidate = settings.IMAGE_DIR / relative_path
            return _safe_local_candidate(candidate)

    if source.startswith("/images/"):
        relative_path = source.removeprefix("/images/")
        candidate = settings.IMAGE_DIR / relative_path
        return _safe_local_candidate(candidate)

    if source.startswith("images/"):
        relative_path = source.removeprefix("images/")
        candidate = settings.IMAGE_DIR / relative_path
        return _safe_local_candidate(candidate)

    candidate = Path(source).expanduser()
    if candidate.is_absolute():
        return _safe_local_candidate(candidate)

    candidate = settings.IMAGE_DIR / candidate
    return _safe_local_candidate(candidate)


def _is_public_ip(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False

    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
        or ip.is_site_local
    )


def validate_remote_image_url(source: str) -> None:
    parsed = urlparse(source)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Remote image URL must use http or https")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Remote image URL must include a hostname")

    if hostname.lower() == "localhost":
        raise ValueError("Remote image URL cannot target localhost")

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(hostname, parsed.port or 443)
        }
    except OSError as exc:
        raise ValueError(f"Unable to resolve remote image host: {hostname}") from exc

    if not addresses:
        raise ValueError(f"Unable to resolve remote image host: {hostname}")

    if not all(_is_public_ip(address) for address in addresses):
        raise ValueError(
            f"Remote image host resolves to a private or local address: {hostname}"
        )


async def download_remote_image(
    source: str,
    temp_files: list[Path],
) -> Path:
    validate_remote_image_url(source)

    parsed = urlparse(source)
    suffix = Path(parsed.path).suffix or ".img"

    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)

    temp_files.append(temp_path)

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    total_bytes = 0

    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        async with client.stream("GET", source) as response:
            response.raise_for_status()

            with temp_path.open("wb") as destination:
                async for chunk in response.aiter_bytes():
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        raise ValueError(
                            f"Remote image exceeds the configured size limit of "
                            f"{settings.MAX_UPLOAD_MB} MB"
                        )
                    destination.write(chunk)

    return temp_path
