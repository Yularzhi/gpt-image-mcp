from __future__ import annotations

try:
    from fastmcp.server.dependencies import get_http_request
except ModuleNotFoundError:
    def get_http_request():  # type: ignore[override]
        raise RuntimeError("FastMCP is not installed")


def get_client_ip() -> str:
    try:
        request = get_http_request()
    except RuntimeError:
        return "unknown"

    if request.client is None:
        return "unknown"

    return request.client.host or "unknown"
