# AEGIS BE → MCP server (design)

**Date:** 2026-05-18
**Status:** Approved, ready for implementation plan
**Scope:** Expose the AEGIS data portal backend as a Model Context Protocol (MCP) server so LLM clients (Claude Desktop in particular) can search the data portal, retrieve sample/species records, and generate `aegis-download` commands from natural language.

## Goals

- Public, anonymous, read-only MCP server reachable from Claude Desktop's "Add custom connector" flow.
- Hand-written tool surface with descriptions tuned for LLMs — not auto-generated from FastAPI routes.
- A first-class affordance for the bulk downloader: an MCP tool that, given filters, returns the exact `aegis-download` shell command, plus a resource serving the full README.
- Deployed on the same Cloud Run service as the existing BE (`portal.aegisearth.bio`). No new service, no new domain, no new IAM.

## Non-goals

- No authentication / OAuth. The REST API is already public; the MCP surface inherits that posture.
- No write tools. Mirror the read-only nature of the data portal.
- No changes to the `fe/` Dash app or the `downloader/` CLI.
- No separate Cloud Run service or revision split.
- No SSE transport — Streamable HTTP only.

## Architecture

### Topology

Single FastAPI process, single Cloud Run service.

```
Cloud Run service: aegis-be
  └─ FastAPI app
       ├─ /api/* …………………… existing REST routes (unchanged)
       └─ /api/mcp ………………… Streamable HTTP MCP endpoint (NEW)
```

The MCP server is mounted as an ASGI sub-application onto the existing FastAPI app. It shares the `AsyncElasticsearch` client held in `app.state.es_client` so there's exactly one ES connection pool.

### Transport

**Streamable HTTP** (current MCP spec). A single HTTP endpoint that handles JSON-RPC requests and server-initiated streamed messages. Cloud Run terminates TLS, so the public URL is `https://portal.aegisearth.bio/api/mcp`.

Legacy SSE transport is explicitly out of scope.

### Code layout

```
be/
  main.py             # unchanged FastAPI routes; adds app.mount("/api/mcp", mcp_app)
  mcp_server.py       # NEW — MCP tools, resources, server factory
  requirements.txt    # + mcp[cli]>=1.2.0
  tests/
    test_mcp.py       # NEW — exercises each tool against the existing mock_es_client
```

`mcp_server.py` exports a `build_mcp_app(es_client)` factory that returns the Streamable HTTP ASGI app. `main.py`'s `lifespan` constructs it after creating the ES client and mounts it.

The MCP tools call the same query helpers (`elastic_search`, `elastic_details`) used by the REST routes — there is one ES query path, not two.

## MCP surface

### Tools

| Tool | Purpose | Notes |
|---|---|---|
| `search_species` | Search the data portal index | Filters: phylogeny (kingdom/order/family), bioSamplesStatus/rawDataStatus/assembliesStatus/annotationStatus, countries, free-text `q`, paging. Returns top N records and a compact aggregation summary. |
| `get_species` | Fetch one species record by `tax_id` | Returns the full data portal document including `assemblies`, `annotations`, `rawData`, `locations`. |
| `search_samples` | Search the samples index | Filters: `taxId`, country, organismPart, sex, collectingInstitution, free-text. Paged. |
| `get_sample` | Fetch one sample by accession | Returns the full BioSamples-derived record. |
| `aggregate_samples_by_location` | Geo grid aggregation | Takes bounds + zoom (matches the REST `/samples/geo_aggregation`). Returns clusters. |
| `build_bulk_download_command` | Generate `aegis-download` invocation | Takes the same filter arguments the LLM is already using when searching, returns the literal shell command string. This is the "how to use bulk-downloader" entry point. |

Tool descriptions are written for LLMs: they describe *when* to call each tool, what the parameters mean in domain terms, and what the response shape will be. Pydantic models are reused from `be/models.py` for argument validation so the JSON schema in the MCP tool manifest matches the REST API.

### Resources

| URI | Content |
|---|---|
| `bulk-downloader://readme` | The full bulk-downloader README served as text/markdown. Lets MCP clients pull the full doc on demand. Content is inlined as a Python string constant in `mcp_server.py` (see Deployment §2). |

### Prompts

None in v1. (Can be added later, e.g. "summarise species" or "draft a download workflow", once we see how clients use the tools.)

## Error handling

- Tool handlers catch `elasticsearch.ApiError` and raise `mcp.McpError` with a clear message and a non-retryable error code. The LLM sees a useful error string, not a stack trace.
- Schema validation errors from Pydantic surface as MCP errors with `code=invalid_params`.
- The `bulk-downloader://readme` resource is a module-level string constant — no I/O, no cache invalidation, no error path.

## Testing

`be/tests/test_mcp.py` covers each tool by:

1. Constructing an MCP `Server` instance with a mocked `AsyncElasticsearch` (same fixture as the existing endpoint tests).
2. Calling the tool handler directly with sample inputs.
3. Asserting the returned content and the ES query body the mock saw.

This mirrors the existing `test_endpoints.py` style and reuses `mock_es_client` from `conftest.py`. No need to run an MCP client.

## Client integration: Claude Desktop

Once deployed:

1. Claude Desktop → Settings → Connectors → **Add custom connector** → **Remote MCP server**.
2. URL: `https://portal.aegisearth.bio/api/mcp`.
3. Auth: none.
4. Restart Claude Desktop. The six tools and the README resource appear in the tool picker.

Fallback for clients that don't yet support remote Streamable HTTP: install `mcp-remote` from npm and configure it as a stdio MCP server that proxies to the URL. Connection instructions (both the native flow and the `mcp-remote` fallback) live in `docs/mcp.md`, created as part of the implementation.

## Deployment (GCP Cloud Run)

The existing service is rebuilt; no new resources are created.

1. The `mcp` dependency is added to `be/requirements.txt`; the existing `Dockerfile` rebuilds without changes (it does `pip install -r requirements.txt`).
2. `downloader/README.md` is copied into the BE image at build time so the resource handler can read it. The simplest path: add a `COPY ../downloader/README.md /app/bulk_downloader_readme.md` step. Alternative (and cleaner for Cloud Build context): include the README contents inline as a Python string constant in `mcp_server.py`. **Decision: inline the string** — avoids cross-directory build-context contortions and keeps the BE container self-contained.
3. `gcloud run deploy aegis-be --source ./be --region europe-west2 --timeout=3600 --allow-unauthenticated` re-rolls the service. The `--timeout=3600` is the only setting change — Streamable HTTP can hold sessions open longer than the default 300s.
4. Verify with `curl https://portal.aegisearth.bio/api/mcp` (should return an MCP initialization response, not a 404).

Concrete `gcloud` invocations and any required `cloudbuild.yaml` tweaks are in the implementation plan, not in this design doc.

## Open questions

None — all decisions resolved during brainstorming. The README-inlining choice is the only deviation from "obvious path"; it's called out above.
