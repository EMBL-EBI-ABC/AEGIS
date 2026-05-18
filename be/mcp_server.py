# be/mcp_server.py
from elasticsearch import AsyncElasticsearch
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from models import (
    DataPortalSearchParams, DataPortalAggregationResponse, DataPortalData,
)
from queries import data_portal_search_full


_DATA_PORTAL_INDEX = "2026-05-15_data_portal"
_SAMPLES_INDEX = "2026-05-15_samples"

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


@mcp.tool()
async def search_species(
    q: str | None = None,
    kingdom: str | None = None,
    tax_order: str | None = None,
    family: str | None = None,
    countries: str | None = None,
    bioSamplesStatus: str | None = None,
    rawDataStatus: str | None = None,
    assembliesStatus: str | None = None,
    annotationStatus: str | None = None,
    start: int = 0,
    size: int = 10,
) -> dict:
    """Search the AEGIS data portal for biodiversity species records.

    The data portal indexes species along with their genomic assets (raw reads,
    assemblies, annotations) produced by the AEGIS pipeline. Use this to find
    species matching:
      - phylogeny: `kingdom`, `tax_order`, `family` (exact match on the
        normalised taxonomy fields)
      - pipeline progress: `bioSamplesStatus`, `rawDataStatus`,
        `assembliesStatus`, `annotationStatus` (each typically "Done"/"Submitted"/etc.)
      - geographic origin: `countries`
      - free text: `q` (matches across all fields)

    Pagination via `start`/`size` (size up to 1000). After finding interesting
    tax_ids, call `get_species` for full details, or `build_bulk_download_command`
    to produce a CLI command that downloads the matching assets.
    """
    params = DataPortalSearchParams(
        q=q,
        kingdom=kingdom,
        tax_order=tax_order,
        family=family,
        countries=countries,
        bioSamplesStatus=bioSamplesStatus,
        rawDataStatus=rawDataStatus,
        assembliesStatus=assembliesStatus,
        annotationStatus=annotationStatus,
        start=start,
        size=min(size, 1000),
    )
    result = await data_portal_search_full(
        es_client=_get_es(),
        params=params,
        samples_index=_SAMPLES_INDEX,
        data_portal_index=_DATA_PORTAL_INDEX,
        data_class=DataPortalData,
        aggregation_class=DataPortalAggregationResponse,
    )
    return result.model_dump()
