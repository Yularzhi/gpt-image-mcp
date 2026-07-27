from __future__ import annotations

import base64
import time

try:
    from fastmcp.dependencies import CurrentContext
    from fastmcp.server.context import Context
except ModuleNotFoundError:
    class Context:  # type: ignore[override]
        pass

    def CurrentContext():  # type: ignore[override]
        return None

from app.config import settings
from app.logging import get_logger
from app.mcp_server import mcp
from app.models import GenerateImageRequest, ImageResponse
from app.openai_client import client
from app.retries import run_with_retry
from app.request_context import get_client_ip
from app.storage import storage

logger = get_logger(__name__)


@mcp.tool(
    name="generate_image",
    description="Generate image using OpenAI GPT Image.",
)
async def generate_image(
    request: GenerateImageRequest,
    ctx: Context = CurrentContext(),
) -> ImageResponse:
    start = time.perf_counter()
    client_ip = get_client_ip()

    async def _generate():
        return await client.images.generate(
            model="gpt-image-1",
            prompt=request.prompt,
            size=request.size,
            quality=request.quality,
            output_format=request.output_format,
            background=request.background,
        )

    try:
        result = await run_with_retry(
            _generate,
            attempts=settings.OPENAI_RETRY_ATTEMPTS,
            base_delay_seconds=settings.OPENAI_RETRY_BASE_DELAY_SECONDS,
        )

        if not result.data or not result.data[0].b64_json:
            raise RuntimeError("OpenAI image generation returned no image data")

        image_bytes = base64.b64decode(result.data[0].b64_json)
        filename = storage.save_bytes(image_bytes, request.output_format)

        response = ImageResponse(
            url=f"{settings.PUBLIC_URL}/images/{filename}",
            filename=filename,
        )

        logger.info(
            "image_generated",
            extra={
                "tool": "generate_image",
                "client_ip": client_ip,
                "request_id": getattr(ctx, "request_id", None),
                "status": "success",
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                "size": request.size,
                "quality": request.quality,
                "output_format": request.output_format,
                "filename": filename,
            },
        )
        return response
    except Exception:  # noqa: BLE001
        logger.exception(
            "image_generation_failed",
            extra={
                "tool": "generate_image",
                "client_ip": client_ip,
                "request_id": getattr(ctx, "request_id", None),
                "status": "error",
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                "size": request.size,
                "quality": request.quality,
                "output_format": request.output_format,
            },
        )
        raise
