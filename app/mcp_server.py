from contextlib import asynccontextmanager

try:
    from fastmcp import FastMCP
except ModuleNotFoundError:
    class FastMCP:  # type: ignore[override]
        def __init__(self, name: str, instructions: str = ""):
            self.name = name
            self.instructions = instructions

        def tool(self, name: str, description: str = ""):
            def decorator(func):
                return func

            return decorator

        @asynccontextmanager
        async def lifespan(self, app):
            yield

        def http_app(self, path: str = "/"):
            async def app(scope, receive, send):
                if scope["type"] == "http":
                    await send(
                        {
                            "type": "http.response.start",
                            "status": 200,
                            "headers": [(b"content-type", b"application/json")],
                        }
                    )
                    await send(
                        {
                            "type": "http.response.body",
                            "body": b'{"status":"ok"}',
                        }
                    )

            return app


mcp = FastMCP(
    name="GPT Image MCP",
    instructions="""
Generate and edit images using OpenAI gpt-image-1.
Always return image URLs.
""".strip(),
)
