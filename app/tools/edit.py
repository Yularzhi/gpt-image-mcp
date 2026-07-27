import base64
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import httpx

from app.config import settings
from app.mcp_server import mcp
from app.models import EditImageRequest, ImageResponse
from app.openai_client import client
from app.storage import storage


def _resolve_local_reference(source: str) -> Path | None:
    public_url = settings.PUBLIC_URL.rstrip("/")

    if public_url:
        public_prefix = f"{public_url}/images/"
        if source.startswith(public_prefix):
            return Path(settings.IMAGE_DIR) / source.removeprefix(public_prefix)

    if source.startswith("/images/"):
        return Path(settings.IMAGE_DIR) / source.removeprefix("/images/")

    if source.startswith("images/"):
        return Path(settings.IMAGE_DIR) / source.removeprefix("images/")

    candidate = Path(source)
    if candidate.exists():
        return candidate

    candidate = Path(settings.IMAGE_DIR) / source
    if candidate.exists():
        return candidate

    return None


async def _materialize_image_source(
    source: str,
    temp_files: list[Path],
) -> Path:
    resolved = _resolve_local_reference(source)
    if resolved is not None:
        return resolved

    if source.startswith(("http://", "https://")):
        parsed = urlparse(source)
        suffix = Path(parsed.path).suffix or ".img"

        async with httpx.AsyncClient(timeout=60) as http_client:
            response = await http_client.get(source)
            response.raise_for_status()

        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(response.content)
            temp_path = Path(tmp.name)

        temp_files.append(temp_path)
        return temp_path

    raise FileNotFoundError(f"Image source not found: {source}")


@mcp.tool(
    name="edit_image",
    description="Edit one or more images using OpenAI GPT Image edit API."
)
async def edit_image(
    request: EditImageRequest,
) -> ImageResponse:
    temp_files: list[Path] = []

    try:
        image_paths = [
            await _materialize_image_source(source, temp_files)
            for source in request.input_images
        ]

        edit_kwargs = {
            "model": "gpt-image-1",
            "image": image_paths,
            "prompt": request.prompt,
            "size": request.size,
            "quality": request.quality,
            "output_format": request.output_format,
            "background": request.background,
        }

        if request.mask:
            edit_kwargs["mask"] = await _materialize_image_source(
                request.mask,
                temp_files,
            )

        result = await client.images.edit(**edit_kwargs)

        if not result.data or not result.data[0].b64_json:
            raise RuntimeError("OpenAI image edit returned no image data")

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        filename = storage.save_bytes(
            image_bytes,
            request.output_format,
        )

        public_url = settings.PUBLIC_URL.rstrip("/")

        return ImageResponse(
            url=f"{public_url}/images/{filename}",
            filename=filename,
        )
    finally:
        for temp_file in temp_files:
            with suppress(FileNotFoundError):
                temp_file.unlink()
