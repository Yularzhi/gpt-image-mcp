try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:
    class BaseModel:
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self):
            return dict(self.__dict__)

    def Field(default=None, **kwargs):  # type: ignore[override]
        return default


class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1)

    size: str = "1024x1024"

    quality: str = "high"

    output_format: str = "png"

    background: str = "auto"


class EditImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1)

    input_images: list[str] = Field(..., min_length=1)

    mask: str | None = None

    size: str = "1024x1024"

    quality: str = "high"

    output_format: str = "png"

    background: str = "auto"


class ImageResponse(BaseModel):
    url: str

    filename: str

    width: int | None = None

    height: int | None = None
