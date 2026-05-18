from unittest.mock import AsyncMock
import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.fixture
def mock_es_client():
    client = AsyncMock()
    return client


@pytest.fixture
async def client(mock_es_client):
    app.state.es_client = mock_es_client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def mcp_http_session():
    """Provide a running MCP HTTP session for integration tests.

    Calls ``build_mcp_app()`` to get a *fresh* Starlette app backed by a new
    ``StreamableHTTPSessionManager`` (the manager enforces a one-shot invariant,
    so each test needs its own).  The fresh app is temporarily remounted at
    ``/api/mcp`` for the duration of the test, then restored on teardown.

    Yields a dict with:
      - ``ac``: an AsyncClient pointed at the test app
      - ``session_id``: the MCP session-id from the initialize handshake
      - ``headers``: the base MCP request headers
      - ``init_resp``: the raw initialize response
    """
    import starlette.routing as sr
    from mcp_server import set_es_client, build_mcp_app
    from main import app

    es = AsyncMock()
    set_es_client(es)
    app.state.es_client = es

    # Build a fresh MCP app (new session manager) and temporarily remount it.
    fresh_mcp_app = build_mcp_app()
    mount_entry = None
    original_app = None
    for route in app.routes:
        if isinstance(route, sr.Mount) and route.path == "/api/mcp":
            mount_entry = route
            original_app = route.app
            route.app = fresh_mcp_app
            break

    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }

    try:
        transport = ASGITransport(app=app)
        async with fresh_mcp_app.router.lifespan_context(app):
            async with AsyncClient(
                transport=transport,
                base_url="http://test",
                follow_redirects=True,
            ) as ac:
                init_resp = await ac.post(
                    "/api/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "id": 0,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-03-26",
                            "capabilities": {},
                            "clientInfo": {"name": "fixture", "version": "0.0"},
                        },
                    },
                    headers=headers,
                )
                assert init_resp.status_code == 200, f"MCP initialize failed: {init_resp.text}"
                session_id = None
                for k, v in init_resp.headers.items():
                    if k.lower() == "mcp-session-id":
                        session_id = v
                        break
                assert session_id, f"No mcp-session-id header in: {dict(init_resp.headers)}"

                await ac.post(
                    "/api/mcp",
                    json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
                    headers={**headers, "mcp-session-id": session_id},
                )

                yield {"ac": ac, "session_id": session_id, "headers": headers, "init_resp": init_resp}
    finally:
        if mount_entry is not None and original_app is not None:
            mount_entry.app = original_app
