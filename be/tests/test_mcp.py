import pytest
from unittest.mock import AsyncMock
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_mcp_module_imports_and_exposes_factory():
    """The mcp_server module exposes build_mcp_app() and set_es_client()."""
    from mcp_server import build_mcp_app, set_es_client
    set_es_client(AsyncMock())
    asgi_app = build_mcp_app()
    assert asgi_app is not None


@pytest.mark.anyio
async def test_mcp_endpoint_responds_to_initialize(mock_es_client):
    """POST a JSON-RPC `initialize` to /api/mcp; expect a 200 with a session header.

    This test uses its own client so it can run the MCP session-manager lifespan
    (via mcp_app.router.lifespan_context) alongside the HTTP request. The shared
    `client` fixture in conftest.py bypasses the FastAPI lifespan to avoid real
    Elasticsearch connections; that pattern doesn't work here because the MCP
    session manager requires its task group to be initialised before requests arrive.
    """
    from main import app, mcp_app
    from mcp_server import set_es_client
    set_es_client(mock_es_client)
    app.state.es_client = mock_es_client

    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "0.0"},
        },
    }
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    transport = ASGITransport(app=app)
    async with mcp_app.router.lifespan_context(app):
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            follow_redirects=True,
        ) as ac:
            response = await ac.post("/api/mcp", json=body, headers=headers)
    assert response.status_code == 200
    assert "mcp-session-id" in {k.lower() for k in response.headers.keys()}
