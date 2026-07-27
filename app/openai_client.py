from app.config import settings

try:
    from openai import AsyncOpenAI
except ModuleNotFoundError:
    class _MissingImages:
        async def generate(self, **kwargs):
            raise RuntimeError("openai package is not installed")

    class AsyncOpenAI:  # type: ignore[override]
        def __init__(self, api_key: str):
            self.api_key = api_key
            self.images = _MissingImages()


client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
)
