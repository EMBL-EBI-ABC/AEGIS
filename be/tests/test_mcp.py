import pytest
from unittest.mock import AsyncMock


@pytest.mark.anyio
async def test_mcp_module_imports_and_exposes_factory():
    """The mcp_server module exposes build_mcp_app() and set_es_client()."""
    from mcp_server import build_mcp_app, set_es_client
    set_es_client(AsyncMock())
    asgi_app = build_mcp_app()
    assert asgi_app is not None


@pytest.mark.anyio
async def test_mcp_endpoint_responds_to_initialize(mcp_http_session):
    """POST a JSON-RPC `initialize` to /api/mcp; expect a 200 with a session header.

    Uses the `mcp_http_session` fixture which manages the StreamableHTTPSessionManager
    lifespan (which can only be started once per instance) and performs the initialize
    handshake, yielding the response and session-id for assertions.
    """
    init_resp = mcp_http_session["init_resp"]
    assert init_resp.status_code == 200
    assert "mcp-session-id" in {k.lower() for k in init_resp.headers.keys()}


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


@pytest.mark.anyio
async def test_search_samples_queries_samples_index():
    from mcp_server import search_samples, set_es_client

    es = AsyncMock()
    es.search.return_value = {
        "hits": {"total": {"value": 0}, "hits": []},
        "aggregations": {
            "collectingInstitution": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "country": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "organismPart": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "sex": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "taxId": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
        },
    }
    set_es_client(es)

    result = await search_samples(taxId=6344, country="United Kingdom", size=5)
    assert es.search.call_args.kwargs["index"] == "2026-05-15_samples"
    body = es.search.call_args.kwargs["body"]
    filters = body["query"]["bool"]["filter"]
    assert {"terms": {"taxId": [6344]}} in filters
    assert {"terms": {"country": ["United Kingdom"]}} in filters
    assert result["total"] == 0


@pytest.mark.anyio
async def test_get_sample_returns_record_by_accession():
    from mcp_server import get_sample, set_es_client

    es = AsyncMock()
    es.search.return_value = {"hits": {"hits": [{"_source": {
        "accession": "SAMEA7522340", "taxId": 6344, "scientificName": "Hirudo medicinalis",
        "commonName": None, "trackingSystem": "COPO", "projectTag": None, "projectName": None,
        "organismPart": None, "lifestage": None, "sex": None, "collectedBy": None,
        "collectionDate": None, "collectionDateText": None, "locality": None,
        "country": None, "habitat": None, "collectingInstitution": None,
        "location": None, "elevation": None, "tolid": None, "specimenVoucher": None,
        "derivedFrom": "SAMEA7522339", "sampleSymbiontOf": None, "symbiont": None,
        "relationship": None, "sampleSameAs": None, "sampleCollectionMethod": None,
        "identifiedBy": None, "identifierAffiliation": None, "sampleCoordinator": None,
        "sampleCoordinatorAffiliation": None, "barcodingCenter": None, "gal": None,
        "specimenId": None, "galSampleId": None, "proxyVoucher": None,
        "proxyBiomaterial": None, "bioMaterial": None, "cultureOrStrainId": None,
        "originalCollectionDate": None, "originalCollectionDateText": None,
        "originalGeographicLocation": None, "originalLatitude": None,
        "originalLongitude": None, "sraAccession": None, "insdcCenterName": None,
        "insdcStatus": None, "insdcFirstPublic": None, "insdcLastUpdate": None,
        "latitudeStart": None, "longitudeStart": None, "latitudeEnd": None,
        "longitudeEnd": None, "depth": None, "customFields": None,
    }}]}}
    set_es_client(es)

    result = await get_sample(accession="SAMEA7522340")
    assert result["results"][0]["accession"] == "SAMEA7522340"
    assert es.search.call_args.kwargs["index"] == "2026-05-15_samples"
    assert es.search.call_args.kwargs["q"] == "_id:SAMEA7522340"


@pytest.mark.anyio
async def test_aggregate_samples_by_location_returns_clusters():
    from mcp_server import aggregate_samples_by_location, set_es_client

    es = AsyncMock()
    es.search.return_value = {"aggregations": {"grid": {"buckets": [
        {"key": "5/16/10", "doc_count": 42, "centroid": {"location": {"lat": 51.5, "lon": -0.1}}},
    ]}}}
    set_es_client(es)

    result = await aggregate_samples_by_location(zoom=5)
    assert len(result["clusters"]) == 1
    assert result["clusters"][0]["count"] == 42
    assert result["clusters"][0]["lat"] == 51.5
    assert es.search.call_args.kwargs["index"] == "2026-05-15_samples"


def test_build_bulk_download_command_basic():
    from mcp_server import build_bulk_download_command

    cmd = build_bulk_download_command(tax_id="43171", types="assemblies", output="./linaria")
    assert cmd["command"].startswith("aegis-download")
    assert "--tax-id 43171" in cmd["command"]
    assert "--type assemblies" in cmd["command"]
    assert "--output ./linaria" in cmd["command"]


def test_build_bulk_download_command_quotes_shell_unsafe_args():
    from mcp_server import build_bulk_download_command

    cmd = build_bulk_download_command(q="Homo sapiens; rm -rf /")
    # The dangerous payload must be inside single quotes so the shell treats
    # it as a literal string.
    assert "'Homo sapiens; rm -rf /'" in cmd["command"]


def test_build_bulk_download_command_explains_filters():
    from mcp_server import build_bulk_download_command

    cmd = build_bulk_download_command(order="Lepidoptera", types="annotations,raw-data", dry_run=True)
    assert "--order Lepidoptera" in cmd["command"]
    assert "--type annotations,raw-data" in cmd["command"]
    assert "--dry-run" in cmd["command"]
    assert "explanation" in cmd
    assert "Lepidoptera" in cmd["explanation"]


def test_bulk_downloader_readme_resource_returns_full_text():
    from mcp_server import bulk_downloader_readme
    from bulk_downloader_docs import README_TEXT

    content = bulk_downloader_readme()
    assert content == README_TEXT
    assert "aegis-download" in content
    assert "## Flags" in content


@pytest.mark.anyio
async def test_mcp_endpoint_lists_all_tools(mcp_http_session):
    """Initialize a session, then call tools/list — expect all six tools.

    Uses the `mcp_http_session` fixture which manages the StreamableHTTPSessionManager
    lifespan (started exactly once) so this test can make a follow-up request without
    hitting the "run() can only be called once" restriction on the shared session manager.
    """
    ac = mcp_http_session["ac"]
    session_id = mcp_http_session["session_id"]
    headers = mcp_http_session["headers"]

    list_resp = await ac.post(
        "/api/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        headers={**headers, "mcp-session-id": session_id},
    )
    assert list_resp.status_code == 200

    text = list_resp.text
    for name in [
        "search_species",
        "get_species",
        "search_samples",
        "get_sample",
        "aggregate_samples_by_location",
        "build_bulk_download_command",
    ]:
        assert name in text, f"tool {name!r} not advertised; response (first 500 chars): {text[:500]}"
