import base64

from app.config import settings
from app.mcp_server import mcp
from app.models import GenerateImageRequest, ImageResponse
from app.openai_client import client
from app.storage import storage


@mcp.tool(
    name="generate_image",
    description="Generate image using OpenAI GPT Image."
)
async def generate_image(
    request: GenerateImageRequest,
) -> ImageResponse:
    result = await client.images.generate(
        model="gpt-image-1",
        prompt=request.prompt,
        size=request.size,
        quality=request.quality,
        output_format=request.output_format,
        background=request.background,
    )

    if not result.data or not result.data[0].b64_json:
        raise RuntimeError("OpenAI image generation returned no image data")

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
