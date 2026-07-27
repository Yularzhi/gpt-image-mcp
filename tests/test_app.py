import asyncio
import base64
import importlib
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from app.models import GenerateImageRequest


class AppTests(unittest.TestCase):
    def test_health_tool_returns_ok(self):
        health_module = importlib.import_module("app.tools.health")

        result = asyncio.run(health_module.health())

        self.assertEqual(
            result,
            {
                "status": "ok",
                "service": "gpt-image-mcp",
            },
        )

    def test_storage_saves_bytes_with_normalized_extension(self):
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["PUBLIC_URL"] = "https://example.com"

        storage_module = importlib.import_module("app.storage")
        storage = storage_module.Storage()

        with tempfile.TemporaryDirectory() as temp_dir:
            storage.directory = Path(temp_dir)
            filename = storage.save_bytes(b"abc123", ".PNG")

            self.assertTrue(filename.endswith(".png"))
            self.assertEqual((storage.directory / filename).read_bytes(), b"abc123")

    def test_generate_image_returns_public_url(self):
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["PUBLIC_URL"] = "https://example.com/"

        generate_module = importlib.import_module("app.tools.generate")

        with tempfile.TemporaryDirectory() as temp_dir:
            generate_module.storage.directory = Path(temp_dir)
            generate_module.client = SimpleNamespace(
                images=SimpleNamespace(
                    generate=_fake_generate_image,
                )
            )

            request = GenerateImageRequest(
                prompt="A small cat in watercolor",
                output_format="png",
            )

            response = asyncio.run(generate_module.generate_image(request))

            self.assertTrue(response.url.startswith("https://example.com/images/"))
            self.assertTrue(response.filename.endswith(".png"))
            self.assertEqual(
                (generate_module.storage.directory / response.filename).read_bytes(),
                b"fake-image-bytes",
            )


async def _fake_generate_image(**kwargs):
    return SimpleNamespace(
        data=[
            SimpleNamespace(
                b64_json=base64.b64encode(b"fake-image-bytes").decode("ascii")
            )
        ]
    )
