# MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the AEGIS data portal backend as a public MCP server (Streamable HTTP transport) on the same Cloud Run service as the REST API, with six hand-tuned tools, one resource, and Claude Desktop connection docs.

**Architecture:** Add `be/mcp_server.py` that builds a `FastMCP` server and exposes a `streamable_http_app()` ASGI sub-app. Mount it at `/api/mcp` on the existing FastAPI instance. Extract the query helpers from `main.py` into a `queries.py` module so both the REST routes and the MCP tools share one ES query path. Share the `AsyncElasticsearch` client via a module-level holder populated from the FastAPI lifespan.

**Tech Stack:** Python 3.12, FastAPI, `mcp` SDK (>=1.2, `FastMCP` + Streamable HTTP), `elasticsearch[async]`, pytest with `anyio` + `httpx.AsyncClient`, Google Cloud Run.

**Spec:** `docs/superpowers/specs/2026-05-18-mcp-server-design.md`

---

## File structure

| File | Role |
|---|---|
| `be/queries.py` (NEW) | All ES query logic — `elastic_search`, `elastic_details`, `data_portal_search_full`, `samples_geo_aggregation_query`. Takes `es_client` as parameter (no module state). |
| `be/main.py` (MODIFY) | Route handlers become thin wrappers around `queries.py`. Lifespan also boots the MCP app. New `app.mount("/api/mcp", mcp_app)`. |
| `be/mcp_server.py` (NEW) | `FastMCP("aegis")` instance, six `@mcp.tool` definitions, one `@mcp.resource`, `set_es_client()` setter, `build_mcp_app()` factory. |
| `be/bulk_downloader_docs.py` (NEW) | One constant: `README_TEXT` — verbatim copy of `downloader/README.md`. |
| `be/requirements.txt` (MODIFY) | Add `mcp[cli]>=1.2.0`. |
| `be/tests/test_queries.py` (NEW) | Tests for the extracted query helpers — direct calls, no HTTP. |
| `be/tests/test_mcp.py` (NEW) | Tests for each MCP tool — direct calls on the tool functions with mock ES, plus one end-to-end HTTP test of the `/api/mcp` initialize handshake. |
| `docs/mcp.md` (NEW) | User-facing doc: Claude Desktop "Add custom connector" flow + `mcp-remote` fallback. |

The existing `be/tests/test_endpoints.py` and `be/tests/test_models.py` are unchanged. After Task 1 they still pass because the route handlers delegate to `queries.py` and the route signatures are preserved.

---

## Task 1: Extract query helpers into `be/queries.py`

Refactor with no behavior change. Existing tests must keep passing.

**Files:**
- Create: `be/queries.py`
- Modify: `be/main.py` (lines 69–358 replaced with thin route wrappers)
- Test: `be/tests/test_queries.py` (new, covers helpers directly)

- [ ] **Step 1.1: Write a failing test for the new helper module**

Create `be/tests/test_queries.py`:

```python
import pytest
from unittest.mock import AsyncMock

from queries import elastic_search, elastic_details
from models import DataPortalSearchParams, DataPortalAggregationResponse, DataPortalData


@pytest.mark.anyio
async def test_elastic_search_builds_filter_from_params():
    """elastic_search should pass `bioSamplesStatus` from params into the ES query body."""
    es = AsyncMock()
    es.search.return_value = {
        "hits": {"total": {"value": 0}, "hits": []},
        "aggregations": {
            "bioSamplesStatus": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "rawDataStatus": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "assembliesStatus": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "annotationStatus": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "countries": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
        },
    }
    params = DataPortalSearchParams(bioSamplesStatus="Done")
    result = await elastic_search(
        es_client=es,
        index_name="some_index",
        params=params,
        data_class=DataPortalData,
        aggregation_class=DataPortalAggregationResponse,
    )
    body = es.search.call_args.kwargs["body"]
    assert {"terms": {"bioSamplesStatus": ["Done"]}} in body["query"]["bool"]["filter"]
    assert result.total == 0


@pytest.mark.anyio
async def test_elastic_details_quotes_record_id():
    """elastic_details should url-quote the record id when querying."""
    es = AsyncMock()
    es.search.return_value = {"hits": {"hits": [{"_source": {"taxId": 42, "scientificName": "X", "phylogeny": None, "currentStatus": "X", "currentStatusOrder": 1, "rawData": [], "assemblies": [], "annotations": None, "bioSamplesStatus": "X", "rawDataStatus": "X", "assembliesStatus": "X", "annotationStatus": None, "commonName": None, "sampleCount": None, "locations": None, "countries": None}}]}}
    await elastic_details(es_client=es, index_name="x", record_id="some/id", data_class=DataPortalData)
    assert es.search.call_args.kwargs["q"] == "_id:some%2Fid"
```

- [ ] **Step 1.2: Run the test, confirm it fails on import**

```bash
cd be && source venv/bin/activate
pytest tests/test_queries.py -v
```

Expected: `ModuleNotFoundError: No module named 'queries'`.

- [ ] **Step 1.3: Create `be/queries.py` with `elastic_search` and `elastic_details`**

```python
# be/queries.py
import urllib.parse
from collections import defaultdict
from fastapi import HTTPException

from models import (
    get_list_of_aggregations,
    ElasticResponse,
    ElasticDetailsResponse,
)


async def elastic_search(
    *,
    es_client,
    index_name: str,
    params,
    data_class,
    aggregation_class,
    additional_aggs: dict | None = None,
    additional_filters: list | None = None,
):
    if params.q:
        query_body = {"multi_match": {"query": params.q, "fields": ["*"]}}
    else:
        query_body = {"match_all": {}}

    filters = []
    aggregation_fields = get_list_of_aggregations(aggregation_class)
    if aggregation_fields:
        for aggregation_field in aggregation_fields:
            filter_value = getattr(params, aggregation_field)
            if filter_value:
                if isinstance(filter_value, list):
                    filters.append({"terms": {aggregation_field: filter_value}})
                else:
                    filters.append({"terms": {aggregation_field: [filter_value]}})

    if additional_filters:
        filters.extend(additional_filters)

    search_body = {
        "from": params.start,
        "size": params.size,
        "query": {"bool": {"must": query_body, "filter": filters}},
        "aggs": defaultdict(dict),
    }

    if aggregation_fields:
        for aggregation_field in aggregation_fields:
            search_body["aggs"][aggregation_field] = {"terms": {"field": aggregation_field}}

    if additional_aggs:
        search_body["aggs"].update(additional_aggs)

    search_body["sort"] = [{params.sort_field: {"order": params.sort_order}}]

    try:
        response = await es_client.search(index=index_name, body=search_body)
        total = response["hits"]["total"]["value"]
        hits = [r["_source"] for r in response["hits"]["hits"]]
        aggregations = response["aggregations"]
        return ElasticResponse[data_class, aggregation_class](
            total=total, start=params.start, size=params.size,
            results=hits, aggregations=aggregations,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


async def elastic_details(*, es_client, index_name: str, record_id: str, data_class):
    try:
        response = await es_client.search(
            index=index_name, q=f"_id:{urllib.parse.quote(record_id)}"
        )
        hits = [r["_source"] for r in response["hits"]["hits"]]
        return ElasticDetailsResponse[data_class](results=hits)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
```

- [ ] **Step 1.4: Run the unit tests, confirm they pass**

```bash
pytest tests/test_queries.py -v
```

Expected: both tests PASS.

- [ ] **Step 1.5: Add `data_portal_search_full` and `samples_geo_aggregation_query` to `queries.py`**

Append to `be/queries.py`:

```python
async def data_portal_search_full(*, es_client, params, samples_index: str, data_portal_index: str, data_class, aggregation_class):
    """Data-portal-specific extras: taxonomy aggregations + cross-index geo expansion."""
    additional_aggs = {
        "kingdom": {"terms": {"field": "phylogeny.kingdom.keyword"}},
        "tax_order": {"terms": {"field": "phylogeny.order.keyword"}},
        "family": {"terms": {"field": "phylogeny.family.keyword"}},
    }
    additional_filters = []
    if params.kingdom:
        additional_filters.append({"terms": {"phylogeny.kingdom.keyword": [params.kingdom]}})
    if params.tax_order:
        additional_filters.append({"terms": {"phylogeny.order.keyword": [params.tax_order]}})
    if params.family:
        additional_filters.append({"terms": {"phylogeny.family.keyword": [params.family]}})

    if params.has_bounds():
        geo_query = {
            "size": 0,
            "query": {"bool": {"filter": {"geo_bounding_box": {"location": {
                "top_left": {"lat": params.top_left_lat, "lon": params.top_left_lon},
                "bottom_right": {"lat": params.bottom_right_lat, "lon": params.bottom_right_lon},
            }}}}},
            "aggs": {"tax_ids": {"terms": {"field": "taxId", "size": 10000}}},
        }
        geo_response = await es_client.search(index=samples_index, body=geo_query)
        tax_ids = [b["key"] for b in geo_response["aggregations"]["tax_ids"]["buckets"]]
        additional_filters.append({"terms": {"taxId": tax_ids if tax_ids else [-1]}})

    return await elastic_search(
        es_client=es_client,
        index_name=data_portal_index,
        params=params,
        data_class=data_class,
        aggregation_class=aggregation_class,
        additional_aggs=additional_aggs,
        additional_filters=additional_filters if additional_filters else None,
    )


async def samples_geo_aggregation_query(*, es_client, params, samples_index: str):
    from models import GeoCluster, GeoAggregationResponse

    precision = min(max(params.zoom + 2, 4), 12)

    filters = []
    must = []
    if params.has_bounds():
        filters.append({"geo_bounding_box": {"location": {
            "top_left": {"lat": params.top_left_lat, "lon": params.top_left_lon},
            "bottom_right": {"lat": params.bottom_right_lat, "lon": params.bottom_right_lon},
        }}})
    if params.tax_id is not None:
        filters.append({"term": {"taxId": params.tax_id}})
    if params.tax_ids:
        id_list = [int(x.strip()) for x in params.tax_ids.split(",") if x.strip()]
        if id_list:
            filters.append({"terms": {"taxId": id_list}})
    if params.country:
        filters.append({"term": {"country": params.country}})
    if params.trackingSystem:
        filters.append({"term": {"trackingSystem": params.trackingSystem}})
    if params.q:
        must.append({"multi_match": {"query": params.q, "fields": ["*"]}})

    if filters or must:
        query = {"bool": {}}
        if filters:
            query["bool"]["filter"] = filters
        if must:
            query["bool"]["must"] = must
    else:
        query = {"match_all": {}}

    search_body = {
        "size": 0,
        "query": query,
        "aggs": {"grid": {"geotile_grid": {"field": "location", "precision": precision},
                          "aggs": {"centroid": {"geo_centroid": {"field": "location"}}}}},
    }

    try:
        response = await es_client.search(index=samples_index, body=search_body)
        clusters = [
            GeoCluster(
                lat=b["centroid"]["location"]["lat"],
                lon=b["centroid"]["location"]["lon"],
                count=b["doc_count"],
                key=b["key"],
            )
            for b in response["aggregations"]["grid"]["buckets"]
        ]
        return GeoAggregationResponse(clusters=clusters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geo aggregation error: {str(e)}")
```

- [ ] **Step 1.6: Rewrite `be/main.py` routes to delegate to `queries.py`**

Replace the body of `be/main.py` from line 69 through the end of the route definitions (keep the `lifespan`, `app`, `api` router declaration, and `app.include_router(api)` line). The new route bodies:

```python
# be/main.py (replace from line 68 onward, keeping `api = APIRouter(prefix="/api")` above)
import os
import urllib.parse
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, FastAPI, Query, Path
from elasticsearch import AsyncElasticsearch
from fastapi.middleware.cors import CORSMiddleware

from models import (
    ElasticResponse, ElasticDetailsResponse,
    DataPortalData, DataPortalSearchParams, DataPortalAggregationResponse,
    SampleData, SampleSearchParams, SampleAggregationResponse,
    GeoAggregationParams, GeoAggregationResponse,
)
from queries import (
    elastic_search, elastic_details,
    data_portal_search_full, samples_geo_aggregation_query,
)


DATA_PORTAL_INDEX = "2026-05-15_data_portal"
SAMPLES_INDEX = "2026-05-15_samples"


@asynccontextmanager
async def lifespan(app: FastAPI):
    es_client = AsyncElasticsearch(
        [os.getenv("ES_URL")],
        http_auth=(os.getenv("ES_USERNAME"), os.getenv("ES_PASSWORD")),
        verify_certs=True,
    )
    app.state.es_client = es_client
    yield
    await es_client.close()


app = FastAPI(
    lifespan=lifespan,
    title="AEGIS Data Portal API",
    version="0.0.1",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    license_info={"name": "Apache 2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0.html"},
)
api = APIRouter(prefix="/api")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@api.get("/data_portal")
async def data_portal_search(
    params: Annotated[DataPortalSearchParams, Query()],
) -> ElasticResponse[DataPortalData, DataPortalAggregationResponse]:
    return await data_portal_search_full(
        es_client=app.state.es_client,
        params=params,
        samples_index=SAMPLES_INDEX,
        data_portal_index=DATA_PORTAL_INDEX,
        data_class=DataPortalData,
        aggregation_class=DataPortalAggregationResponse,
    )


@api.get("/data_portal/{record_id}")
async def data_portal_details(
    record_id: Annotated[str, Path(description="Record ID")],
) -> ElasticDetailsResponse[DataPortalData]:
    return await elastic_details(
        es_client=app.state.es_client,
        index_name=DATA_PORTAL_INDEX,
        record_id=record_id,
        data_class=DataPortalData,
    )


@api.get("/samples")
async def samples_search(
    params: Annotated[SampleSearchParams, Query()],
) -> ElasticResponse[SampleData, SampleAggregationResponse]:
    return await elastic_search(
        es_client=app.state.es_client,
        index_name=SAMPLES_INDEX,
        params=params,
        data_class=SampleData,
        aggregation_class=SampleAggregationResponse,
    )


@api.get("/samples/geo_aggregation")
async def samples_geo_aggregation(
    params: Annotated[GeoAggregationParams, Query()],
) -> GeoAggregationResponse:
    return await samples_geo_aggregation_query(
        es_client=app.state.es_client,
        params=params,
        samples_index=SAMPLES_INDEX,
    )


@api.get("/samples/{accession}")
async def samples_details(
    accession: Annotated[str, Path(description="Sample accession")],
) -> ElasticDetailsResponse[SampleData]:
    return await elastic_details(
        es_client=app.state.es_client,
        index_name=SAMPLES_INDEX,
        record_id=accession,
        data_class=SampleData,
    )


app.include_router(api)
```

- [ ] **Step 1.7: Run the full BE test suite, confirm nothing regressed**

```bash
pytest -v
```

Expected: all tests in `test_endpoints.py`, `test_models.py`, `test_queries.py` PASS.

- [ ] **Step 1.8: Commit**

```bash
git add be/queries.py be/main.py be/tests/test_queries.py
git commit -m "Extract ES query helpers into be/queries.py"
```

---

## Task 2: Add MCP dependency and scaffold the MCP module

**Files:**
- Modify: `be/requirements.txt`
- Modify: `be/requirements-dev.txt`
- Create: `be/mcp_server.py`
- Create: `be/bulk_downloader_docs.py`
- Test: `be/tests/test_mcp.py` (new file, will grow per tool)

- [ ] **Step 2.1: Add `mcp` to `be/requirements.txt`**

Append:
```
mcp[cli]>=1.2.0
```

- [ ] **Step 2.2: Install it**

```bash
cd be && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Expected: `mcp` and its dependencies install without error. Verify with `python -c "from mcp.server.fastmcp import FastMCP; print(FastMCP)"`.

- [ ] **Step 2.3: Write a failing import test**

Create `be/tests/test_mcp.py`:

```python
import pytest
from unittest.mock import AsyncMock


@pytest.mark.anyio
async def test_mcp_module_imports_and_exposes_factory():
    """The mcp_server module exposes build_mcp_app() and set_es_client()."""
    from mcp_server import build_mcp_app, set_es_client
    set_es_client(AsyncMock())
    asgi_app = build_mcp_app()
    assert asgi_app is not None
```

- [ ] **Step 2.4: Run, confirm failure**

```bash
pytest tests/test_mcp.py::test_mcp_module_imports_and_exposes_factory -v
```

Expected: `ModuleNotFoundError: No module named 'mcp_server'`.

- [ ] **Step 2.5: Create `be/bulk_downloader_docs.py`**

```python
# be/bulk_downloader_docs.py
"""The aegis-download README, inlined as a string so it ships in the BE container."""

README_TEXT = """# aegis-downloader

Bulk-download AEGIS data portal content (raw reads, assemblies, annotations, samples metadata), filtered by data type and phylogeny.

## Install

```bash
cd downloader
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Quick start

Download all data types for one species:

```bash
aegis-download --tax-id 43171 --output ./aegis-data
```

Download annotations only for all *Lepidoptera*:

```bash
aegis-download --type annotations --order Lepidoptera --output ./lepidoptera
```

Preview what would be downloaded without fetching anything:

```bash
aegis-download --type raw-data --kingdom Animalia --dry-run
```

## Flags

| Flag | Default | Notes |
|---|---|---|
| `--type` | all four | `raw-data`, `assemblies`, `annotations`, `samples-metadata` (comma-separated) |
| `--kingdom` / `--order` / `--family` | — | Phylogeny filters |
| `--tax-id` | — | Comma-separated explicit tax IDs |
| `--country` | — | Country filter (passthrough to BE `countries`) |
| `-q` / `--query` | — | Full-text search |
| `--output` | `./aegis-data` | Output root directory |
| `--workers` | 8 | Concurrent downloads (capped at 32) |
| `--backend-url` | `https://portal.aegisearth.bio/api` | Or set `AEGIS_BACKEND_URL` |
| `--dry-run` | false | Build manifest without downloading |
| `--manifest` | `manifest.tsv` under `--output` | Manifest output path |
| `--manifest-format` | `tsv` | Or `json` |
| `--no-resume` | resume on | Skip the resume check, redownload everything |
| `--max-retries` | 3 | Per-file retries with exponential backoff |
| `--log-level` | `info` | `debug` / `info` / `warning` / `error` |

## Data types

- **`raw-data`** — gzipped FASTQ run files from ENA (paired-end split by `;` in `fastq_ftp`).
- **`assemblies`** — gzipped FASTA of every sequence per assembly, fetched from ENA's browser API.
- **`annotations`** — Ensembl Rapid Release annotation bundles, grouped by assembly name.
- **`samples-metadata`** — TSV dump of BioSamples records associated with the selected species.

## Output layout

```
<output>/
  manifest.tsv
  samples_metadata.tsv          # if samples-metadata is requested
  by_species/
    43171_linaria_vulgaris/
      metadata.json
      raw_data/
        ERR10828371_1.fastq.gz
        ERR10828371_2.fastq.gz
      assemblies/
        GCA_948329855.1.fasta.gz
      annotations/
        daLinVulg1.1/
          <annotation files>
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success (or dry-run completed) |
| 1 | One or more files failed after retries |
| 2 | Invalid arguments |
| 3 | BE unreachable / planning aborted |

## Pagination ceiling

The AEGIS BE caps result-set pagination at 10 000 records. If your filter matches more, the tool exits with a clear error — narrow the filter (e.g. add `--order` or `--family`) and retry.
"""
```

- [ ] **Step 2.6: Create `be/mcp_server.py` skeleton**

```python
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
```

- [ ] **Step 2.7: Run the test, confirm it passes**

```bash
pytest tests/test_mcp.py::test_mcp_module_imports_and_exposes_factory -v
```

Expected: PASS.

- [ ] **Step 2.8: Commit**

```bash
git add be/requirements.txt be/mcp_server.py be/bulk_downloader_docs.py be/tests/test_mcp.py
git commit -m "Scaffold MCP server module and bulk-downloader docs constant"
```

---

## Task 3: Mount MCP app on FastAPI and chain lifespans

The Streamable HTTP ASGI app has its own session-manager lifespan that must run alongside FastAPI's. Mount-then-lifespan is the trickier wiring.

**Files:**
- Modify: `be/main.py`
- Test: `be/tests/test_mcp.py` (add HTTP smoke test)

- [ ] **Step 3.1: Write a failing HTTP smoke test**

Append to `be/tests/test_mcp.py`:

```python
@pytest.mark.anyio
async def test_mcp_endpoint_responds_to_initialize(client, mock_es_client):
    """POST a JSON-RPC `initialize` to /api/mcp; expect a 200 with a session header."""
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
    response = await client.post("/api/mcp", json=body, headers=headers)
    assert response.status_code == 200
    assert "mcp-session-id" in {k.lower() for k in response.headers.keys()}
```

- [ ] **Step 3.2: Run, confirm it 404s**

```bash
pytest tests/test_mcp.py::test_mcp_endpoint_responds_to_initialize -v
```

Expected: FAIL with 404 — `/api/mcp` is not mounted yet.

- [ ] **Step 3.3: Update `be/main.py` to mount the MCP app and chain lifespans**

Edit the top of `be/main.py`. Change the imports and the `lifespan` function:

```python
import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, FastAPI, Query, Path
from elasticsearch import AsyncElasticsearch
from fastapi.middleware.cors import CORSMiddleware

from models import (
    ElasticResponse, ElasticDetailsResponse,
    DataPortalData, DataPortalSearchParams, DataPortalAggregationResponse,
    SampleData, SampleSearchParams, SampleAggregationResponse,
    GeoAggregationParams, GeoAggregationResponse,
)
from queries import (
    elastic_search, elastic_details,
    data_portal_search_full, samples_geo_aggregation_query,
)
from mcp_server import build_mcp_app, set_es_client


DATA_PORTAL_INDEX = "2026-05-15_data_portal"
SAMPLES_INDEX = "2026-05-15_samples"

mcp_app = build_mcp_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastMCP's Streamable HTTP app has its own session-manager lifespan.
    # Nest it inside ours so both run at startup/shutdown.
    async with mcp_app.router.lifespan_context(app):
        es_client = AsyncElasticsearch(
            [os.getenv("ES_URL")],
            http_auth=(os.getenv("ES_USERNAME"), os.getenv("ES_PASSWORD")),
            verify_certs=True,
        )
        app.state.es_client = es_client
        set_es_client(es_client)
        try:
            yield
        finally:
            await es_client.close()


app = FastAPI(
    lifespan=lifespan,
    title="AEGIS Data Portal API",
    version="0.0.1",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    license_info={"name": "Apache 2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0.html"},
)
api = APIRouter(prefix="/api")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
```

Keep the existing route definitions below. After `app.include_router(api)`, add:

```python
app.mount("/api/mcp", mcp_app)
```

- [ ] **Step 3.4: Run, confirm the test passes**

```bash
pytest tests/test_mcp.py::test_mcp_endpoint_responds_to_initialize -v
```

Expected: PASS. If it fails with a session-manager error, double-check that `mcp_app.router.lifespan_context(app)` is the correct API for the installed `mcp` version — `mcp.__version__` ≥ 1.2 is required.

- [ ] **Step 3.5: Run the full suite to make sure REST routes still work**

```bash
pytest -v
```

Expected: every test PASS.

- [ ] **Step 3.6: Commit**

```bash
git add be/main.py be/tests/test_mcp.py
git commit -m "Mount MCP Streamable HTTP app at /api/mcp"
```

---

## Task 4: Implement `search_species` tool

**Files:**
- Modify: `be/mcp_server.py`
- Test: `be/tests/test_mcp.py`

- [ ] **Step 4.1: Write the failing test**

Append to `be/tests/test_mcp.py` (above the HTTP test if helpful, for readability):

```python
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

    result = await search_species.fn(kingdom="Animalia", size=10)

    # The data_portal index should be the one queried.
    indices_seen = [c.kwargs.get("index") for c in es.search.call_args_list]
    assert "2026-05-15_data_portal" in indices_seen

    assert result["total"] == 1
    assert result["results"][0]["scientificName"] == "Hirudo medicinalis"
```

Note: `search_species.fn` exposes the underlying coroutine (FastMCP wraps it). If your `mcp` version exposes it differently, use `search_species.__wrapped__` or just import the unwrapped function.

- [ ] **Step 4.2: Run, confirm failure**

```bash
pytest tests/test_mcp.py::test_search_species_returns_results_and_calls_data_portal_index -v
```

Expected: `ImportError` or `AttributeError: module 'mcp_server' has no attribute 'search_species'`.

- [ ] **Step 4.3: Implement `search_species` in `be/mcp_server.py`**

Append to `be/mcp_server.py`:

```python
from models import (
    DataPortalSearchParams, DataPortalAggregationResponse, DataPortalData,
)
from queries import data_portal_search_full


_DATA_PORTAL_INDEX = "2026-05-15_data_portal"
_SAMPLES_INDEX = "2026-05-15_samples"


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
```

- [ ] **Step 4.4: Run, confirm test passes**

```bash
pytest tests/test_mcp.py::test_search_species_returns_results_and_calls_data_portal_index -v
```

Expected: PASS. If `search_species.fn` doesn't resolve, replace with the unwrapped function reference per your `mcp` SDK version (commonly `search_species.fn` for FastMCP ≥ 1.2).

- [ ] **Step 4.5: Commit**

```bash
git add be/mcp_server.py be/tests/test_mcp.py
git commit -m "MCP tool: search_species"
```

---

## Task 5: Implement `get_species` tool

**Files:**
- Modify: `be/mcp_server.py`
- Test: `be/tests/test_mcp.py`

- [ ] **Step 5.1: Write the failing test**

Append to `be/tests/test_mcp.py`:

```python
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

    result = await get_species.fn(tax_id=43171)
    assert len(result["results"]) == 1
    assert result["results"][0]["taxId"] == 43171
    call = es.search.call_args
    assert call.kwargs["index"] == "2026-05-15_data_portal"
    assert call.kwargs["q"] == "_id:43171"
```

- [ ] **Step 5.2: Run, confirm failure**

```bash
pytest tests/test_mcp.py::test_get_species_returns_full_record -v
```

Expected: `AttributeError` — tool not defined.

- [ ] **Step 5.3: Implement `get_species`**

Append to `be/mcp_server.py`:

```python
from queries import elastic_details


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
```

- [ ] **Step 5.4: Run, confirm test passes**

```bash
pytest tests/test_mcp.py::test_get_species_returns_full_record -v
```

Expected: PASS.

- [ ] **Step 5.5: Commit**

```bash
git add be/mcp_server.py be/tests/test_mcp.py
git commit -m "MCP tool: get_species"
```

---

## Task 6: Implement `search_samples` tool

**Files:**
- Modify: `be/mcp_server.py`
- Test: `be/tests/test_mcp.py`

- [ ] **Step 6.1: Write the failing test**

Append to `be/tests/test_mcp.py`:

```python
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

    result = await search_samples.fn(taxId=6344, country="United Kingdom", size=5)
    assert es.search.call_args.kwargs["index"] == "2026-05-15_samples"
    body = es.search.call_args.kwargs["body"]
    filters = body["query"]["bool"]["filter"]
    assert {"terms": {"taxId": [6344]}} in filters
    assert {"terms": {"country": ["United Kingdom"]}} in filters
    assert result["total"] == 0
```

- [ ] **Step 6.2: Run, confirm failure**

```bash
pytest tests/test_mcp.py::test_search_samples_queries_samples_index -v
```

Expected: `AttributeError` — tool not defined.

- [ ] **Step 6.3: Implement `search_samples`**

Append to `be/mcp_server.py`:

```python
from models import SampleSearchParams, SampleAggregationResponse, SampleData
from queries import elastic_search


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
```

- [ ] **Step 6.4: Run, confirm test passes**

```bash
pytest tests/test_mcp.py::test_search_samples_queries_samples_index -v
```

Expected: PASS.

- [ ] **Step 6.5: Commit**

```bash
git add be/mcp_server.py be/tests/test_mcp.py
git commit -m "MCP tool: search_samples"
```

---

## Task 7: Implement `get_sample` tool

**Files:**
- Modify: `be/mcp_server.py`
- Test: `be/tests/test_mcp.py`

- [ ] **Step 7.1: Write the failing test**

Append to `be/tests/test_mcp.py`:

```python
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

    result = await get_sample.fn(accession="SAMEA7522340")
    assert result["results"][0]["accession"] == "SAMEA7522340"
    assert es.search.call_args.kwargs["index"] == "2026-05-15_samples"
    assert es.search.call_args.kwargs["q"] == "_id:SAMEA7522340"
```

- [ ] **Step 7.2: Run, confirm failure**

```bash
pytest tests/test_mcp.py::test_get_sample_returns_record_by_accession -v
```

Expected: `AttributeError`.

- [ ] **Step 7.3: Implement `get_sample`**

Append to `be/mcp_server.py`:

```python
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
```

- [ ] **Step 7.4: Run, confirm test passes**

```bash
pytest tests/test_mcp.py::test_get_sample_returns_record_by_accession -v
```

Expected: PASS.

- [ ] **Step 7.5: Commit**

```bash
git add be/mcp_server.py be/tests/test_mcp.py
git commit -m "MCP tool: get_sample"
```

---

## Task 8: Implement `aggregate_samples_by_location` tool

**Files:**
- Modify: `be/mcp_server.py`
- Test: `be/tests/test_mcp.py`

- [ ] **Step 8.1: Write the failing test**

Append to `be/tests/test_mcp.py`:

```python
@pytest.mark.anyio
async def test_aggregate_samples_by_location_returns_clusters():
    from mcp_server import aggregate_samples_by_location, set_es_client

    es = AsyncMock()
    es.search.return_value = {"aggregations": {"grid": {"buckets": [
        {"key": "5/16/10", "doc_count": 42, "centroid": {"location": {"lat": 51.5, "lon": -0.1}}},
    ]}}}
    set_es_client(es)

    result = await aggregate_samples_by_location.fn(zoom=5)
    assert len(result["clusters"]) == 1
    assert result["clusters"][0]["count"] == 42
    assert result["clusters"][0]["lat"] == 51.5
    assert es.search.call_args.kwargs["index"] == "2026-05-15_samples"
```

- [ ] **Step 8.2: Run, confirm failure**

```bash
pytest tests/test_mcp.py::test_aggregate_samples_by_location_returns_clusters -v
```

Expected: `AttributeError`.

- [ ] **Step 8.3: Implement `aggregate_samples_by_location`**

Append to `be/mcp_server.py`:

```python
from models import GeoAggregationParams
from queries import samples_geo_aggregation_query


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
```

- [ ] **Step 8.4: Run, confirm test passes**

```bash
pytest tests/test_mcp.py::test_aggregate_samples_by_location_returns_clusters -v
```

Expected: PASS.

- [ ] **Step 8.5: Commit**

```bash
git add be/mcp_server.py be/tests/test_mcp.py
git commit -m "MCP tool: aggregate_samples_by_location"
```

---

## Task 9: Implement `build_bulk_download_command` tool

Pure function, no ES. This is the "how to use bulk-downloader" entry point: the LLM gives the user's filters, we render the exact `aegis-download` shell command.

**Files:**
- Modify: `be/mcp_server.py`
- Test: `be/tests/test_mcp.py`

- [ ] **Step 9.1: Write the failing tests**

Append to `be/tests/test_mcp.py`:

```python
def test_build_bulk_download_command_basic():
    from mcp_server import build_bulk_download_command

    cmd = build_bulk_download_command.fn(tax_id="43171", types="assemblies", output="./linaria")
    assert cmd["command"].startswith("aegis-download")
    assert "--tax-id 43171" in cmd["command"]
    assert "--type assemblies" in cmd["command"]
    assert "--output ./linaria" in cmd["command"]


def test_build_bulk_download_command_quotes_shell_unsafe_args():
    from mcp_server import build_bulk_download_command

    cmd = build_bulk_download_command.fn(q="Homo sapiens; rm -rf /")
    # The dangerous payload must be inside single quotes so the shell treats
    # it as a literal string.
    assert "'Homo sapiens; rm -rf /'" in cmd["command"]


def test_build_bulk_download_command_explains_filters():
    from mcp_server import build_bulk_download_command

    cmd = build_bulk_download_command.fn(order="Lepidoptera", types="annotations,raw-data", dry_run=True)
    assert "--order Lepidoptera" in cmd["command"]
    assert "--type annotations,raw-data" in cmd["command"]
    assert "--dry-run" in cmd["command"]
    assert "explanation" in cmd
    assert "Lepidoptera" in cmd["explanation"]
```

- [ ] **Step 9.2: Run, confirm failure**

```bash
pytest tests/test_mcp.py::test_build_bulk_download_command_basic tests/test_mcp.py::test_build_bulk_download_command_quotes_shell_unsafe_args tests/test_mcp.py::test_build_bulk_download_command_explains_filters -v
```

Expected: `AttributeError` — tool not defined.

- [ ] **Step 9.3: Implement `build_bulk_download_command`**

Append to `be/mcp_server.py`:

```python
import shlex


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
```

- [ ] **Step 9.4: Run, confirm tests pass**

```bash
pytest tests/test_mcp.py::test_build_bulk_download_command_basic tests/test_mcp.py::test_build_bulk_download_command_quotes_shell_unsafe_args tests/test_mcp.py::test_build_bulk_download_command_explains_filters -v
```

Expected: all three PASS.

- [ ] **Step 9.5: Commit**

```bash
git add be/mcp_server.py be/tests/test_mcp.py
git commit -m "MCP tool: build_bulk_download_command"
```

---

## Task 10: Implement `bulk-downloader://readme` resource

**Files:**
- Modify: `be/mcp_server.py`
- Test: `be/tests/test_mcp.py`

- [ ] **Step 10.1: Write the failing test**

Append to `be/tests/test_mcp.py`:

```python
def test_bulk_downloader_readme_resource_returns_full_text():
    from mcp_server import bulk_downloader_readme
    from bulk_downloader_docs import README_TEXT

    content = bulk_downloader_readme.fn()
    assert content == README_TEXT
    assert "aegis-download" in content
    assert "## Flags" in content
```

- [ ] **Step 10.2: Run, confirm failure**

```bash
pytest tests/test_mcp.py::test_bulk_downloader_readme_resource_returns_full_text -v
```

Expected: `AttributeError`.

- [ ] **Step 10.3: Implement the resource**

Append to `be/mcp_server.py`:

```python
from bulk_downloader_docs import README_TEXT


@mcp.resource("bulk-downloader://readme")
def bulk_downloader_readme() -> str:
    """The full aegis-download CLI README, including flags, output layout, exit codes, and pagination notes."""
    return README_TEXT
```

- [ ] **Step 10.4: Run, confirm test passes**

```bash
pytest tests/test_mcp.py::test_bulk_downloader_readme_resource_returns_full_text -v
```

Expected: PASS.

- [ ] **Step 10.5: Run the entire BE test suite once more**

```bash
pytest -v
```

Expected: all tests PASS — REST endpoints, query helpers, MCP tools, MCP resource, MCP HTTP handshake.

- [ ] **Step 10.6: Commit**

```bash
git add be/mcp_server.py be/tests/test_mcp.py
git commit -m "MCP resource: bulk-downloader://readme"
```

---

## Task 11: End-to-end MCP `tools/list` smoke test

Verify the mounted MCP app advertises all six tools over HTTP. This guards against silent regressions where a tool decorator is missing or wired up incorrectly.

**Files:**
- Test: `be/tests/test_mcp.py`

- [ ] **Step 11.1: Write the failing test**

Append to `be/tests/test_mcp.py`:

```python
@pytest.mark.anyio
async def test_mcp_endpoint_lists_all_tools(client, mock_es_client):
    """Initialize a session, then call tools/list — expect all six tools."""
    init_body = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "test", "version": "0.0"},
        },
    }
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    init_resp = await client.post("/api/mcp", json=init_body, headers=headers)
    session_id = init_resp.headers.get("mcp-session-id") or init_resp.headers.get("Mcp-Session-Id")
    assert session_id

    list_body = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    list_resp = await client.post(
        "/api/mcp",
        json=list_body,
        headers={**headers, "mcp-session-id": session_id},
    )
    assert list_resp.status_code == 200
    # Streamable HTTP can return either application/json or an SSE stream.
    # Grab the body and look for tool names — robust to either encoding.
    text = list_resp.text
    for name in [
        "search_species",
        "get_species",
        "search_samples",
        "get_sample",
        "aggregate_samples_by_location",
        "build_bulk_download_command",
    ]:
        assert name in text, f"tool {name} not advertised: {text[:500]}"
```

- [ ] **Step 11.2: Run, confirm it passes**

```bash
pytest tests/test_mcp.py::test_mcp_endpoint_lists_all_tools -v
```

Expected: PASS — all six tools registered on the FastMCP instance show up in the `tools/list` response.

If it fails because of session handling differences in the installed `mcp` version, the corrective action is to update the test to match the actual session-header casing/flow, not to weaken the assertion that all six tool names appear.

- [ ] **Step 11.3: Commit**

```bash
git add be/tests/test_mcp.py
git commit -m "End-to-end MCP smoke test: tools/list advertises all six tools"
```

---

## Task 12: Write `docs/mcp.md` connection guide

User-facing documentation: how to point Claude Desktop at the deployed MCP server, plus the `mcp-remote` fallback.

**Files:**
- Create: `docs/mcp.md`

- [ ] **Step 12.1: Create `docs/mcp.md`**

```markdown
# AEGIS MCP server

The AEGIS data portal is available as a Model Context Protocol (MCP) server so
that LLM clients (Claude Desktop and others) can search species, retrieve
samples, generate bulk-download commands, and read the downloader documentation
directly inside a chat.

- **Endpoint:** `https://portal.aegisearth.bio/api/mcp`
- **Transport:** Streamable HTTP (MCP spec 2025-03-26)
- **Auth:** none (public read-only)

## Tools

| Tool | What it does |
|---|---|
| `search_species` | Filter the data portal by phylogeny, status, country, free text. |
| `get_species` | Full record for one `tax_id`. |
| `search_samples` | Filter the samples index by tax_id, country, organism part, etc. |
| `get_sample` | Full record for one BioSamples accession. |
| `aggregate_samples_by_location` | Geo-grid cluster counts for a map view. |
| `build_bulk_download_command` | Render the exact `aegis-download` CLI command for the user's filters. |

## Resources

| URI | Content |
|---|---|
| `bulk-downloader://readme` | Full `aegis-download` README (install, flags, output layout). |

## Connecting Claude Desktop

1. Open Claude Desktop.
2. **Settings → Connectors → Add custom connector → Remote MCP server**.
3. Set the URL to `https://portal.aegisearth.bio/api/mcp`. Leave auth blank.
4. Save and restart Claude Desktop.
5. The six tools appear in the tool picker; you can call them from any chat.

## Fallback: `mcp-remote`

If your client doesn't yet support remote Streamable HTTP, use the `mcp-remote`
stdio→HTTP proxy:

```json
{
  "mcpServers": {
    "aegis": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://portal.aegisearth.bio/api/mcp"]
    }
  }
}
```

Drop that into your client's MCP servers config and restart.

## Local development

To exercise the MCP server against a local BE:

```bash
cd be
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080
# In another shell, point a client at:
#   http://localhost:8080/api/mcp
```
```

- [ ] **Step 12.2: Commit**

```bash
git add docs/mcp.md
git commit -m "Add docs/mcp.md connection guide"
```

---

## Task 13: Deploy to Google Cloud Run

Re-deploy the existing `aegis-be` Cloud Run service with the MCP additions. No new infrastructure is created.

**Files:**
- Verify: `be/Dockerfile` (no change needed; `pip install -r requirements.txt` picks up `mcp`)

- [ ] **Step 13.1: Verify the Dockerfile builds locally**

```bash
cd be
docker build -t aegis-be-local:mcp .
```

Expected: build succeeds and `mcp` is installed in the image. Verify:

```bash
docker run --rm aegis-be-local:mcp python -c "from mcp.server.fastmcp import FastMCP; print('mcp ok')"
```

Expected: prints `mcp ok`.

- [ ] **Step 13.2: Confirm the gcloud project/service**

```bash
gcloud config get-value project
gcloud run services list --region europe-west2
```

Expected: the project is the one running AEGIS; the list shows the existing BE service (likely `aegis-be`).

- [ ] **Step 13.3: Deploy from source**

```bash
cd be
gcloud run deploy aegis-be \
  --source . \
  --region europe-west2 \
  --allow-unauthenticated \
  --timeout=3600 \
  --concurrency=80 \
  --set-env-vars ES_URL=$ES_URL,ES_USERNAME=$ES_USERNAME,ES_PASSWORD=$ES_PASSWORD
```

Notes:
- `--timeout=3600` is the only change from the existing config — Streamable HTTP sessions can stay open longer than the 300s default.
- If `ES_URL` / `ES_USERNAME` / `ES_PASSWORD` are already set on the service, drop the `--set-env-vars` flag to leave them as they are.
- Substitute the actual service name from Step 13.2 if it differs.

Expected: the deploy completes and prints a service URL.

- [ ] **Step 13.4: Smoke-test the live REST API**

```bash
curl -s "https://portal.aegisearth.bio/api/data_portal?size=1" | head -c 200
```

Expected: a JSON response with `"total":` — confirms REST routes still work after the refactor.

- [ ] **Step 13.5: Smoke-test the MCP endpoint**

```bash
curl -i -X POST https://portal.aegisearth.bio/api/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"0.0"}}}'
```

Expected: HTTP 200, a `Mcp-Session-Id` response header, and a JSON-RPC initialize result in the body listing the server's capabilities (tools, resources).

- [ ] **Step 13.6: Connect Claude Desktop**

Open Claude Desktop → **Settings → Connectors → Add custom connector → Remote MCP server** → URL: `https://portal.aegisearth.bio/api/mcp`. Save, restart, and verify the tool picker shows the six AEGIS tools. Sanity check by calling `search_species` with `kingdom: Plantae, size: 3` from a fresh chat.

- [ ] **Step 13.7: Commit any final adjustments**

If steps 13.1–13.6 surfaced no issues, no further commits are needed. Otherwise, address them and commit.

```bash
git status
# if clean, nothing to do.
```

---

## Self-review

(For the planning agent — not the engineer executing this plan.)

**Spec coverage check:**

- Tool surface (6 tools): Tasks 4, 5, 6, 7, 8, 9 ✓
- Resource (`bulk-downloader://readme`): Task 10 ✓
- Streamable HTTP transport: Tasks 2, 3, 11 ✓
- Shared ES query path: Task 1 (refactor to `queries.py`) ✓
- Mount on existing FastAPI under `/api/mcp`: Task 3 ✓
- README inlined as Python string: Task 2 (creates `bulk_downloader_docs.py`) ✓
- Claude Desktop / `mcp-remote` instructions: Task 12 ✓
- GCP Cloud Run deploy with `--timeout=3600`: Task 13 ✓
- No auth: implicit (no auth-related code in any task) ✓
- No write tools: implicit (no mutation in any tool) ✓

**Placeholder scan:** none found. Every step contains the literal code or command.

**Type / name consistency check:**
- `set_es_client` / `_get_es` / `build_mcp_app` used consistently across Tasks 2, 3, 4+.
- `_DATA_PORTAL_INDEX` / `_SAMPLES_INDEX` constants defined in Task 4 and reused in Tasks 5, 6, 7, 8.
- `data_portal_search_full` / `elastic_search` / `elastic_details` / `samples_geo_aggregation_query` defined in Task 1 and referenced by name in Tasks 3, 4, 5, 6, 7, 8.
- Tool decorator pattern (`@mcp.tool()`, `.fn` accessor in tests) consistent across Tasks 4–9.

No drift detected.
