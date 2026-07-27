import asyncio
import importlib.util
import os
import unittest


@unittest.skipIf(
    importlib.util.find_spec("fastmcp") is None
    or importlib.util.find_spec("fastapi") is None,
    "FastMCP/FastAPI dependencies are not installed",
)
class MCPIntegrationTests(unittest.TestCase):
    def setUp(self):
        os.environ.setdefault("OPENAI_API_KEY", "test-key")
        os.environ.setdefault("PUBLIC_URL", "https://example.com")

    def test_all_tools_are_registered_on_mcp_instance(self):
        from fastmcp.client import Client

        import app.main
        from app.mcp_server import mcp

        async def list_tool_names():
            async with Client(mcp) as client:
                tools = await client.list_tools()
                return {tool.name for tool in tools}

        self.assertEqual(
            asyncio.run(list_tool_names()),
            {"generate_image", "edit_image", "health"},
        )

    def test_mcp_post_route_is_published(self):
        from fastapi.testclient import TestClient

        import app.main

        headers = {
            "accept": "application/json, text/event-stream",
            "content-type": "application/json",
        }

        with TestClient(app.main.app) as client:
            response = client.post("/mcp/", headers=headers, json={})

        self.assertNotEqual(response.status_code, 404)
