from __future__ import annotations

try:
    from fastmcp.dependencies import CurrentContext
    from fastmcp.server.context import Context
except ModuleNotFoundError:
    class Context:  # type: ignore[override]
        pass

    def CurrentContext():  # type: ignore[override]
        return None

from app.logging import get_logger
from app.mcp_server import mcp
from app.request_context import get_client_ip

logger = get_logger(__name__)


@mcp.tool(
    name="health",
    description="Check server health.",
)
async def health(ctx: Context = CurrentContext()):
    logger.info(
        "health_check",
        extra={
            "tool": "health",
            "client_ip": get_client_ip(),
            "request_id": getattr(ctx, "request_id", None),
            "status": "success",
        },
    )
    return {
        "status": "ok",
        "service": "gpt-image-mcp",
    }
