import os
from pathlib import Path

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


class Settings(BaseModel):
    OPENAI_API_KEY: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))

    HOST: str = "0.0.0.0"
    PORT: int = 8080

    PUBLIC_URL: str = Field(default_factory=lambda: os.getenv("PUBLIC_URL", ""))

    IMAGE_DIR: Path = Path(os.getenv("IMAGE_DIR", "data/images"))

    LOG_LEVEL: str = "INFO"


settings = Settings(
    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
    PUBLIC_URL=os.getenv("PUBLIC_URL", ""),
)
