from app.mcp_server import mcp


@mcp.tool(
    name="health",
    description="Check server health."
)
async def health():

    return {
        "status": "ok",
        "service": "gpt-image-mcp",
    }