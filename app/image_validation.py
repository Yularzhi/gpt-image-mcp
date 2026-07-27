from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.config import settings


@dataclass(slots=True)
class ValidatedImage:
    path: Path
    format: str
    width: int
    height: int
    size_bytes: int


def _max_bytes(limit_mb: int) -> int:
    return limit_mb * 1024 * 1024


def validate_image_file(
    path: Path,
    *,
    allow_mask: bool = False,
    expected_size: tuple[int, int] | None = None,
) -> ValidatedImage:
    if not path.exists():
        raise FileNotFoundError(f"Image file does not exist: {path}")

    size_bytes = path.stat().st_size
    limit_mb = settings.MAX_MASK_MB if allow_mask else settings.MAX_UPLOAD_MB
    if size_bytes > _max_bytes(limit_mb):
        raise ValueError(
            f"Image file is too large: {path.name} is {size_bytes} bytes, "
            f"limit is {limit_mb} MB"
        )

    try:
        with Image.open(path) as image:
            image.verify()

        with Image.open(path) as image:
            image.load()
            format_name = (image.format or "").upper()
            width, height = image.size
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError(f"Unsupported image file: {path}") from exc

    if not format_name:
        raise ValueError(f"Could not detect image format for: {path}")

    if allow_mask:
        if format_name != "PNG":
            raise ValueError("Mask must be a PNG file")
    elif format_name not in {"PNG", "JPEG", "JPG", "WEBP"}:
        raise ValueError(
            f"Unsupported image format for {path.name}: {format_name.lower()}"
        )

    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid image dimensions for {path.name}")

    if width > settings.MAX_IMAGE_EDGE_PX or height > settings.MAX_IMAGE_EDGE_PX:
        raise ValueError(
            f"Image dimensions for {path.name} exceed the configured limit of "
            f"{settings.MAX_IMAGE_EDGE_PX}px"
        )

    if expected_size is not None and (width, height) != expected_size:
        raise ValueError(
            f"Mask dimensions for {path.name} must match the first image "
            f"dimensions {expected_size[0]}x{expected_size[1]}"
        )

    return ValidatedImage(
        path=path,
        format=format_name,
        width=width,
        height=height,
        size_bytes=size_bytes,
    )
