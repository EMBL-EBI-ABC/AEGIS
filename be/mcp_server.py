# be/mcp_server.py
import shlex

from elasticsearch import AsyncElasticsearch
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from models import (
    DataPortalSearchParams, DataPortalAggregationResponse, DataPortalData,
    GeoAggregationParams,
    SampleSearchParams, SampleAggregationResponse, SampleData,
)
from queries import data_portal_search_full, elastic_details, elastic_search, samples_geo_aggregation_query


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


@mcp.tool()
async def get_species(tax_id: int) -> dict:
    """Fetch the full AEGIS data portal record for one species by NCBI tax_id.

    Returns the complete document including:
      - `assemblies`: every genome assembly (accession, version) for this species
      - `annotations`: Ensembl Rapid Release annotation bundles per assembly
      - `rawData`: ENA sequencing run records with `fastq_ftp` paths
      - `sampleCount`, `locations`, `countries`: aggregated sample provenance

    Use after `search_species` to drill into one tax_id. To get all the
    associated BioSamples, call `search_samples(taxId=tax_id)` instead.
    """
    result = await elastic_details(
        es_client=_get_es(),
        index_name=_DATA_PORTAL_INDEX,
        record_id=str(tax_id),
        data_class=DataPortalData,
    )
    return result.model_dump()


@mcp.tool()
async def search_samples(
    q: str | None = None,
    taxId: int | None = None,
    country: str | None = None,
    organismPart: str | None = None,
    sex: str | None = None,
    collectingInstitution: str | None = None,
    start: int = 0,
    size: int = 10,
) -> dict:
    """Search the AEGIS samples index (BioSamples records).

    Each sample is one physical specimen contributed to the AEGIS project, with
    collection metadata (location, collector, organism part, sex, etc.). Filter
    by:
      - `taxId`: the species this sample belongs to (use after search_species)
      - `country`, `organismPart`, `sex`, `collectingInstitution`: discrete filters
      - `q`: free text

    Returns up to `size` records (max 1000). For one specific sample, use
    `get_sample` with its BioSamples accession.
    """
    params = SampleSearchParams(
        q=q,
        taxId=taxId,
        country=country,
        organismPart=organismPart,
        sex=sex,
        collectingInstitution=collectingInstitution,
        start=start,
        size=min(size, 1000),
    )
    result = await elastic_search(
        es_client=_get_es(),
        index_name=_SAMPLES_INDEX,
        params=params,
        data_class=SampleData,
        aggregation_class=SampleAggregationResponse,
    )
    return result.model_dump()


@mcp.tool()
async def get_sample(accession: str) -> dict:
    """Fetch the full AEGIS sample record for one BioSamples accession.

    Returns the complete record including ENA/INSDC provenance, collection
    metadata, derivedFrom relationships, and any custom fields. Use after
    `search_samples` to drill into one specimen.
    """
    result = await elastic_details(
        es_client=_get_es(),
        index_name=_SAMPLES_INDEX,
        record_id=accession,
        data_class=SampleData,
    )
    return result.model_dump()


@mcp.tool()
async def aggregate_samples_by_location(
    zoom: int,
    top_left_lat: float | None = None,
    top_left_lon: float | None = None,
    bottom_right_lat: float | None = None,
    bottom_right_lon: float | None = None,
    tax_id: int | None = None,
    tax_ids: str | None = None,
    q: str | None = None,
    country: str | None = None,
    trackingSystem: str | None = None,
) -> dict:
    """Aggregate AEGIS samples into geographic clusters for a map view.

    Uses an Elasticsearch geotile_grid; grid precision is derived from `zoom`
    (0 = world, 20 = street level). Each returned cluster has `lat`, `lon`
    (centroid), `count`, and an opaque grid `key`. Filters narrow the
    underlying sample set before clustering. Pass bounding-box corners to
    restrict to a viewport, or `tax_id`/`tax_ids` to a single species or set.

    Use this to answer "where are samples concentrated for X species" or
    "what does the world map look like inside this bounding box".
    """
    params = GeoAggregationParams(
        zoom=zoom,
        top_left_lat=top_left_lat,
        top_left_lon=top_left_lon,
        bottom_right_lat=bottom_right_lat,
        bottom_right_lon=bottom_right_lon,
        tax_id=tax_id,
        tax_ids=tax_ids,
        q=q,
        country=country,
        trackingSystem=trackingSystem,
    )
    result = await samples_geo_aggregation_query(
        es_client=_get_es(),
        params=params,
        samples_index=_SAMPLES_INDEX,
    )
    return result.model_dump()


@mcp.tool()
def build_bulk_download_command(
    types: str | None = None,
    tax_id: str | None = None,
    kingdom: str | None = None,
    order: str | None = None,
    family: str | None = None,
    country: str | None = None,
    q: str | None = None,
    output: str = "./aegis-data",
    workers: int | None = None,
    dry_run: bool = False,
) -> dict:
    """Render the exact `aegis-download` shell command for a user's filters.

    Use this whenever the user wants to BULK DOWNLOAD species data they've
    been exploring via `search_species` or `search_samples`. The data portal
    REST/MCP API is fine for inspecting a few records, but for fetching
    actual files (raw FASTQs, assembly FASTAs, annotation bundles), the
    `aegis-download` CLI is the right tool — it handles concurrency, retries,
    resume, and manifest tracking.

    Pass the same filters the user is interested in. The tool returns a
    `command` string (literal shell command) and an `explanation` string
    summarising what it will do. The full CLI README is also available as
    the resource `bulk-downloader://readme`.

    Args:
      types: Comma-separated. Any of: raw-data, assemblies, annotations,
        samples-metadata. Default: all four.
      tax_id: Comma-separated explicit NCBI tax IDs.
      kingdom / order / family: Phylogeny filters.
      country: Country filter.
      q: Free-text search.
      output: Output directory (default ./aegis-data).
      workers: Concurrent downloads (default 8, capped at 32).
      dry_run: Build the manifest without downloading.
    """
    parts = ["aegis-download"]

    def add(flag: str, value):
        if value is None or value == "":
            return
        parts.extend([flag, shlex.quote(str(value))])

    add("--type", types)
    add("--tax-id", tax_id)
    add("--kingdom", kingdom)
    add("--order", order)
    add("--family", family)
    add("--country", country)
    add("-q", q)
    add("--output", output)
    if workers is not None:
        add("--workers", workers)
    if dry_run:
        parts.append("--dry-run")

    command = " ".join(parts)

    filters_described = []
    if tax_id:
        filters_described.append(f"tax_id={tax_id}")
    if kingdom:
        filters_described.append(f"kingdom={kingdom}")
    if order:
        filters_described.append(f"order={order}")
    if family:
        filters_described.append(f"family={family}")
    if country:
        filters_described.append(f"country={country}")
    if q:
        filters_described.append(f"q={q!r}")
    filter_summary = ", ".join(filters_described) or "no filters (everything)"

    type_summary = types or "all four data types (raw-data, assemblies, annotations, samples-metadata)"
    dry_note = " (dry-run: build manifest only, no files downloaded)" if dry_run else ""

    explanation = (
        f"This will run aegis-download against {filter_summary}, fetching "
        f"{type_summary} into {output}{dry_note}. Install the CLI first with "
        f"`pip install -e ./downloader` from the AEGIS repo, then run the command."
    )

    return {"command": command, "explanation": explanation}


from bulk_downloader_docs import README_TEXT


@mcp.resource("bulk-downloader://readme")
def bulk_downloader_readme() -> str:
    """The full aegis-download CLI README, including flags, output layout, exit codes, and pagination notes."""
    return README_TEXT
