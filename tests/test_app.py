import asyncio
import base64
import importlib
import os
from pathlib import Path
from io import BytesIO
import tempfile
import unittest
from types import SimpleNamespace

from PIL import Image

from app.models import EditImageRequest, GenerateImageRequest


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

    def test_edit_image_supports_multiple_inputs_and_mask(self):
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["PUBLIC_URL"] = "https://example.com"

        edit_module = importlib.import_module("app.tools.edit")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            first = temp_path / "first.png"
            second = temp_path / "second.png"
            mask = temp_path / "mask.png"

            first.write_bytes(_png_bytes((255, 0, 0, 255)))
            second.write_bytes(_png_bytes((0, 255, 0, 255)))
            mask.write_bytes(_png_bytes((0, 0, 0, 0)))

            edit_module.settings.PUBLIC_URL = "https://example.com"
            edit_module.settings.IMAGE_DIR = temp_path
            edit_module.storage.directory = temp_path

            captured = {}

            async def _fake_edit_image(**kwargs):
                captured.update(kwargs)
                return SimpleNamespace(
                    data=[
                        SimpleNamespace(
                            b64_json=base64.b64encode(b"edited-image-bytes").decode(
                                "ascii"
                            )
                        )
                    ]
                )

            edit_module.client = SimpleNamespace(
                images=SimpleNamespace(
                    edit=_fake_edit_image,
                )
            )

            request = EditImageRequest(
                prompt="Turn this into a neon poster",
                input_images=[
                    "https://example.com/images/first.png",
                    "second.png",
                ],
                mask="https://example.com/images/mask.png",
                output_format="png",
            )

            response = asyncio.run(edit_module.edit_image(request))

            self.assertEqual(captured["model"], "gpt-image-1")
            self.assertEqual(len(captured["image"]), 2)
            self.assertEqual(captured["image"][0], first)
            self.assertEqual(captured["image"][1], second)
            self.assertEqual(captured["mask"], mask)
            self.assertTrue(response.url.startswith("https://example.com/images/"))
            self.assertTrue(response.filename.endswith(".png"))
            self.assertEqual(
                (edit_module.storage.directory / response.filename).read_bytes(),
                b"edited-image-bytes",
            )


async def _fake_generate_image(**kwargs):
    return SimpleNamespace(
        data=[
            SimpleNamespace(
                b64_json=base64.b64encode(b"fake-image-bytes").decode("ascii")
            )
        ]
    )


def _png_bytes(color: tuple[int, int, int, int]) -> bytes:
    buffer = BytesIO()
    image = Image.new("RGBA", (1, 1), color)
    image.save(buffer, format="PNG")
    return buffer.getvalue()
