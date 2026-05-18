# be/mcp_server.py
from elasticsearch import AsyncElasticsearch
from mcp.server.fastmcp import FastMCP

_es_client: AsyncElasticsearch | None = None


def set_es_client(client: AsyncElasticsearch) -> None:
    """Called from the FastAPI lifespan once the ES connection is open."""
    global _es_client
    _es_client = client


def _get_es() -> AsyncElasticsearch:
    if _es_client is None:
        raise RuntimeError("MCP server: ES client not initialised. Call set_es_client() during FastAPI lifespan startup.")
    return _es_client


mcp = FastMCP("aegis")


def build_mcp_app():
    """Return the Streamable HTTP ASGI app to mount on FastAPI."""
    return mcp.streamable_http_app()
