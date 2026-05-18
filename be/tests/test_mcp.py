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


@pytest.mark.anyio
async def test_search_species_returns_results_and_calls_data_portal_index():
    from mcp_server import search_species, set_es_client

    es = AsyncMock()
    es.search.return_value = {
        "hits": {"total": {"value": 1}, "hits": [{"_source": {
            "taxId": 6344, "scientificName": "Hirudo medicinalis",
            "commonName": "medicinal leech", "phylogeny": None,
            "currentStatus": "Annotation Complete", "currentStatusOrder": 5,
            "bioSamplesStatus": "Done", "rawDataStatus": "Done",
            "assembliesStatus": "Done", "annotationStatus": "Done",
            "rawData": [], "assemblies": [], "annotations": None,
            "sampleCount": 1, "locations": None, "countries": None,
        }}]},
        "aggregations": {
            "bioSamplesStatus": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "rawDataStatus": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "assembliesStatus": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "annotationStatus": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "countries": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
        },
    }
    set_es_client(es)

    # FastMCP's @mcp.tool() decorator returns the original function unchanged,
    # so search_species is the plain async coroutine — call it directly.
    result = await search_species(kingdom="Animalia", size=10)

    # The data_portal index should be the one queried.
    indices_seen = [c.kwargs.get("index") for c in es.search.call_args_list]
    assert "2026-05-15_data_portal" in indices_seen

    assert result["total"] == 1
    assert result["results"][0]["scientificName"] == "Hirudo medicinalis"


@pytest.mark.anyio
async def test_get_species_returns_full_record():
    from mcp_server import get_species, set_es_client

    es = AsyncMock()
    es.search.return_value = {"hits": {"hits": [{"_source": {
        "taxId": 43171, "scientificName": "Linaria vulgaris", "commonName": None,
        "phylogeny": None, "currentStatus": "Annotation Complete", "currentStatusOrder": 5,
        "bioSamplesStatus": "Done", "rawDataStatus": "Done",
        "assembliesStatus": "Done", "annotationStatus": "Done",
        "rawData": [], "assemblies": [], "annotations": None,
        "sampleCount": 1, "locations": None, "countries": None,
    }}]}}
    set_es_client(es)

    result = await get_species(tax_id=43171)
    assert len(result["results"]) == 1
    assert result["results"][0]["taxId"] == 43171
    call = es.search.call_args
    assert call.kwargs["index"] == "2026-05-15_data_portal"
    assert call.kwargs["q"] == "_id:43171"
