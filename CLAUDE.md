# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

Three Python components, each with its own venv and dependencies:

- `be/` — FastAPI backend, deployed behind a proxy at `https://portal.aegisearth.bio/api`. Wraps an Elasticsearch cluster.
- `fe/` — Dash (Plotly) multi-page web app, deployed at `https://aegis-fe-1091670130981.europe-west2.run.app`. Calls the BE over HTTP.
- `downloader/` — `aegis-downloader` CLI (entry point `aegis-download`), a separately-installable Python 3.12+ package that drives the BE's public API to bulk-download raw reads, assemblies, annotations, and samples metadata.

There is no shared root-level package or dependency manifest — each component is built and shipped independently. The FE and downloader are both API clients of the BE.

## Commands

### Backend (`be/`)

```bash
cd be
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Run (requires ES_URL, ES_USERNAME, ES_PASSWORD env vars)
uvicorn main:app --host 0.0.0.0 --port 8080

# Tests (anyio-based async tests; ES is mocked via conftest.py)
pytest -v
pytest tests/test_endpoints.py::test_samples_search -v   # single test
```

### Frontend (`fe/`)

```bash
cd fe
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run (BACKEND_URL defaults to production; override for local BE)
BACKEND_URL=http://localhost:8080/api python app.py
```

No test suite in `fe/`.

### Downloader (`downloader/`)

```bash
cd downloader
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

aegis-download --tax-id 43171 --output ./aegis-data
aegis-download --type annotations --order Lepidoptera --dry-run

pytest -v
pytest tests/test_planner.py -v        # single file
pytest tests/test_planner.py::test_build_plan_skips_records_not_in_explicit_tax_ids -v
```

`pyproject.toml` sets `pythonpath = ["src"]` and `testpaths = ["tests"]`, so `pytest` works from the `downloader/` directory without further config.

## Architecture

### BE: dynamic Pydantic models from a single field definition list

`be/models.py` defines each index as a `DataSource(fields=[FieldDefinition(...)])`. `DataSource.generate_classes()` uses `pydantic.create_model` to synthesize three classes at import time:

- a `Data` model (response row),
- an `AggregationResponse` model with one `Aggregation` field per `filterable=True` field,
- a `SearchParams` subclass that adds a query parameter per filterable field with the right Python type.

Adding a new filterable field on `data_portal` or `samples_source` is therefore a one-line change in `models.py`: it appears in the OpenAPI schema, as a filter on the search endpoint, and as an aggregation in the response automatically. This is why `be/main.py`'s `elastic_search()` is generic and iterates over `get_list_of_aggregations(aggregation_class)`.

**Bounds/taxonomy filters are special.** They sit outside the auto-generated machinery and are handled explicitly in `data_portal_search` via `additional_filters` and `additional_aggs`. The taxonomy aggregations are nested fields (`phylogeny.kingdom.keyword`), and the geo filter does a *cross-index* query: it first hits the samples index with a `geo_bounding_box`, collects matching `taxId`s, then filters the data_portal query down to those tax IDs. The `/samples/geo_aggregation` endpoint uses Elasticsearch's `geotile_grid` with precision derived from the requested map zoom level.

**Index names are date-prefixed and hardcoded.** Search for `2026-05-15_` in `be/main.py` — when the ES index is re-indexed, this prefix has to be updated in every endpoint (currently in three places).

The FastAPI app mounts everything under `/api` (the proxy doesn't strip the prefix) and configures `docs_url="/api/docs"`. CORS is wide open.

### FE: Dash pages auto-registered, BE called over HTTP via `requests`

`fe/app.py` instantiates Dash with `use_pages=True`. Every `*.py` under `fe/pages/` calls `dash.register_page(__name__, path=..., title=...)` at import time, and `dash.page_registry` is read in `app.py` to build the navbar. Adding a new page is two changes: drop a file in `pages/` that registers itself, then add a link in `app.py`'s navbar (it does *not* enumerate the registry — links are hand-listed).

Each page reads `BACKEND_URL = os.getenv("BACKEND_URL", "https://portal.aegisearth.bio/api")` independently and uses synchronous `requests` against it. There is no shared HTTP client. `pages/utils.py` has the only shared helper today (status badges).

Styling: theming uses CSS custom properties in `assets/styles.css` (`var(--aegis-bg-card)`, `var(--font-display)`, etc.). Match these tokens rather than hardcoding colors/fonts when extending pages.

`server = app.server` is exposed for the gunicorn deployment (`gunicorn -b 0.0.0.0:${PORT} app:server`).

### Downloader: plan → execute, BE is the single source of truth

`aegis_downloader/cli.py` wires up the pipeline:

1. `planner.build_plan()` iterates `ApiClient.iter_data_portal(filters=…)`, filters by explicit `--tax-id` if given, and for each species record runs the registered extractors (`extract_raw_data`, `extract_assemblies`, `extract_annotations` in `extractors.py`) to produce a list of `DownloadTask`s. It also queues `MetadataWrite`s (one `metadata.json` per species + an optional combined `samples_metadata.tsv`).
2. `downloader.execute_plan()` writes the manifest, fans the tasks out across a `ThreadPoolExecutor` (default 8 workers, capped at 32), and uses `rich.progress` with one bar per file. Each `_download_one` does an optional HEAD for size, streams the body to a `.partial` file, atomically renames on success, retries with exponential backoff on `HTTPStatusError`/`TransportError`, and skips already-on-disk files when `--resume` is on.
3. `manifest.Manifest` keeps the manifest in memory and rewrites the whole file on every `update()` under a lock (sufficient at current concurrency).

**Key invariants:**
- The downloader **never** queries Elasticsearch directly — it only uses the BE's public REST API. New data types should be added by extending the BE's record shape and adding an extractor function in `extractors.py`.
- `ApiClient._paginate` enforces the 10 000-record ceiling (`MAX_RESULT_WINDOW`) by raising `PaginationCeilingError` *before* paging. This corresponds to Elasticsearch's `index.max_result_window` — CLI exit code 3.
- ENA's FASTA endpoint doesn't return `Content-Length`, so assemblies have `head_supported=False`; the progress bar is unbounded for those.
- Test transports are injected via `httpx.MockTransport` — see `tests/conftest.py` and the `transport=` parameters threaded through `ApiClient` and the `httpx.Client` in `cli.run()`.

### Cross-component contract

The BE response shapes (`results`, `total`, `aggregations`, and the per-field schemas in `be/models.py`) are the de-facto API contract for both the FE and the downloader. Changes there ripple to both clients. There is no shared schema package; consumers parse JSON directly.
