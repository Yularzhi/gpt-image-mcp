from __future__ import annotations

import base64
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse
import time

import httpx

try:
    from fastmcp.dependencies import CurrentContext
    from fastmcp.server.context import Context
except ModuleNotFoundError:
    class Context:  # type: ignore[override]
        pass

    def CurrentContext():  # type: ignore[override]
        return None

from app.config import settings
from app.image_validation import validate_image_file
from app.logging import get_logger
from app.mcp_server import mcp
from app.models import EditImageRequest, ImageResponse
from app.openai_client import client
from app.retries import run_with_retry
from app.request_context import get_client_ip
from app.storage import storage

logger = get_logger(__name__)


def _resolve_local_reference(source: str) -> Path | None:
    public_url = settings.PUBLIC_URL

    if public_url:
        public_prefix = f"{public_url}/images/"
        if source.startswith(public_prefix):
            return settings.IMAGE_DIR / source.removeprefix(public_prefix)

    if source.startswith("/images/"):
        return settings.IMAGE_DIR / source.removeprefix("/images/")

    if source.startswith("images/"):
        return settings.IMAGE_DIR / source.removeprefix("images/")

    candidate = Path(source).expanduser()
    if candidate.exists():
        return candidate

    candidate = settings.IMAGE_DIR / source
    if candidate.exists():
        return candidate

    return None


async def _download_to_tempfile(source: str, temp_files: list[Path]) -> Path:
    parsed = urlparse(source)
    suffix = Path(parsed.path).suffix or ".img"

    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)

    temp_files.append(temp_path)

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    total_bytes = 0

    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client_:
        async with client_.stream("GET", source) as response:
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


async def _materialize_image_source(
    source: str,
    temp_files: list[Path],
) -> Path:
    resolved = _resolve_local_reference(source)
    if resolved is not None:
        return resolved

    if source.startswith(("http://", "https://")):
        return await _download_to_tempfile(source, temp_files)

    raise FileNotFoundError(f"Image source not found: {source}")


@mcp.tool(
    name="edit_image",
    description="Edit one or more images using OpenAI GPT Image edit API.",
)
async def edit_image(
    request: EditImageRequest,
    ctx: Context = CurrentContext(),
) -> ImageResponse:
    temp_files: list[Path] = []
    start = time.perf_counter()
    client_ip = get_client_ip()

    try:
        image_paths = [
            await _materialize_image_source(source, temp_files)
            for source in request.input_images
        ]
        validated_images = [validate_image_file(path) for path in image_paths]
        reference_size = (
            validated_images[0].width,
            validated_images[0].height,
        )

        mask_path: Path | None = None
        if request.mask:
            mask_path = await _materialize_image_source(request.mask, temp_files)
            validate_image_file(
                mask_path,
                allow_mask=True,
                expected_size=reference_size,
            )

        async def _edit():
            edit_kwargs = {
                "model": "gpt-image-1",
                "image": image_paths,
                "prompt": request.prompt,
                "size": request.size,
                "quality": request.quality,
                "output_format": request.output_format,
                "background": request.background,
            }

            if mask_path is not None:
                edit_kwargs["mask"] = mask_path

            return await client.images.edit(**edit_kwargs)

        result = await run_with_retry(
            _edit,
            attempts=settings.OPENAI_RETRY_ATTEMPTS,
            base_delay_seconds=settings.OPENAI_RETRY_BASE_DELAY_SECONDS,
        )

        if not result.data or not result.data[0].b64_json:
            raise RuntimeError("OpenAI image edit returned no image data")

        image_bytes = base64.b64decode(result.data[0].b64_json)
        filename = storage.save_bytes(image_bytes, request.output_format)

        response = ImageResponse(
            url=f"{settings.PUBLIC_URL}/images/{filename}",
            filename=filename,
        )

        logger.info(
            "image_edited",
            extra={
                "tool": "edit_image",
                "client_ip": client_ip,
                "request_id": getattr(ctx, "request_id", None),
                "status": "success",
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                "image_count": len(image_paths),
                "has_mask": bool(request.mask),
                "size": request.size,
                "quality": request.quality,
                "output_format": request.output_format,
                "filename": filename,
            },
        )
        return response
    except Exception:  # noqa: BLE001
        logger.exception(
            "image_edit_failed",
            extra={
                "tool": "edit_image",
                "client_ip": client_ip,
                "request_id": getattr(ctx, "request_id", None),
                "status": "error",
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                "image_count": len(request.input_images),
                "has_mask": bool(request.mask),
                "size": request.size,
                "quality": request.quality,
                "output_format": request.output_format,
            },
        )
        raise
    finally:
        for temp_file in temp_files:
            with suppress(FileNotFoundError):
                temp_file.unlink()
