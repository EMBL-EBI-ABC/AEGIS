# be/mcp_server.py
from elasticsearch import AsyncElasticsearch
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

_es_client: AsyncElasticsearch | None = None


def set_es_client(client: AsyncElasticsearch) -> None:
    """Called from the FastAPI lifespan once the ES connection is open."""
    global _es_client
    _es_client = client


def _get_es() -> AsyncElasticsearch:
    if _es_client is None:
        raise RuntimeError("MCP server: ES client not initialised. Call set_es_client() during FastAPI lifespan startup.")
    return _es_client


# streamable_http_path='/' so the endpoint lives at the Starlette app root;
# FastAPI mounts it at /api/mcp, making the full path /api/mcp/.
# DNS-rebinding protection is disabled here because we embed the MCP app inside
# FastAPI (not run standalone): host-header validation is the reverse-proxy's job.
# Passing an explicit TransportSecuritySettings overrides FastMCP's auto-enable
# logic that would otherwise activate when host="127.0.0.1".
mcp = FastMCP(
    "aegis",
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


def build_mcp_app():
    """Return the Streamable HTTP ASGI app to mount on FastAPI."""
    return mcp.streamable_http_app()
