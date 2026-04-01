# Maps, Facets, and Sample Detail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add geographic maps at three levels (project, species, sample), taxonomy/country facets, sample hierarchy display, and a new sample detail page to the AEGIS data portal.

**Architecture:** Two ES indices (species + samples). Backend gains sample search, sample detail, and geo aggregation endpoints. Frontend uses dash-leaflet for maps with clustered markers. New sample detail page at `/data-portal/<tax_id>/samples/<accession>`.

**Tech Stack:** FastAPI, Elasticsearch 8.x (geo_point, geotile_grid), Pydantic, Dash, dash-leaflet, dash-bootstrap-components

**Spec:** `docs/superpowers/specs/2026-03-31-maps-facets-sample-detail-design.md`

---

## File Structure

**Files to create:**
- `be/tests/__init__.py` — test package
- `be/tests/conftest.py` — ES mock fixtures for FastAPI test client
- `be/tests/test_models.py` — model unit tests
- `be/tests/test_endpoints.py` — endpoint integration tests with mocked ES
- `be/requirements-dev.txt` — test dependencies
- `fe/pages/sample_details.py` — new sample detail page

**Files to modify:**
- `be/models.py` — add sample models, geo models, update data_portal models
- `be/main.py` — add sample/geo endpoints, update data_portal endpoint
- `fe/requirements.txt` — add dash-leaflet
- `fe/pages/data_portal.py` — add map, taxonomy/country facets, sampleCount column
- `fe/pages/data_portal_details.py` — add map, hierarchical samples tab, fetch from samples API

---

### Task 1: Backend — Add sample and geo models to models.py

**Files:**
- Modify: `be/models.py`

- [ ] **Step 1: Add SampleData model using the existing DataSource pattern**

Add below the existing `data_portal` DataSource definition at the end of `be/models.py`:

```python
# Samples.
samples_source = DataSource(
    name="Samples",
    fields=[
        FieldDefinition(name="accession", type=str),
        FieldDefinition(name="taxId", type=int, filterable=True),
        FieldDefinition(name="scientificName", type=str),
        FieldDefinition(name="commonName", type=str),
        FieldDefinition(name="location", type=dict[str, float] | None),
        FieldDefinition(name="country", type=str, filterable=True),
        FieldDefinition(name="locality", type=str | None),
        FieldDefinition(name="habitat", type=str | None),
        FieldDefinition(name="elevation", type=float | None),
        FieldDefinition(name="collectionDate", type=str | None),
        FieldDefinition(name="collectedBy", type=str | None),
        FieldDefinition(name="collectingInstitution", type=str | None, filterable=True),
        FieldDefinition(name="sex", type=str | None, filterable=True),
        FieldDefinition(name="organismPart", type=str | None, filterable=True),
        FieldDefinition(name="lifestage", type=str | None),
        FieldDefinition(name="tolid", type=str | None),
        FieldDefinition(name="derivedFrom", type=str | None),
        FieldDefinition(name="trackingSystem", type=str | None),
        FieldDefinition(name="projectName", type=str | None),
    ],
    default_sort_field="accession",
    default_sort_order="asc",
)
(SampleData, SampleAggregationResponse, SampleSearchParams) = (
    samples_source.generate_classes()
)
```

- [ ] **Step 2: Add GeoAggregation models**

Add below the samples DataSource, still in `be/models.py`:

```python
# Geo aggregation models.


class GeoAggregationParams(BaseModel):
    model_config = {"extra": "forbid"}
    zoom: int = Field(..., ge=0, le=20, description="Map zoom level")
    top_left_lat: float | None = Field(None, description="Bounding box top-left latitude")
    top_left_lon: float | None = Field(None, description="Bounding box top-left longitude")
    bottom_right_lat: float | None = Field(None, description="Bounding box bottom-right latitude")
    bottom_right_lon: float | None = Field(None, description="Bounding box bottom-right longitude")
    tax_id: int | None = Field(None, description="Filter to a specific species")

    def has_bounds(self) -> bool:
        return all(
            v is not None
            for v in [self.top_left_lat, self.top_left_lon, self.bottom_right_lat, self.bottom_right_lon]
        )


class GeoCluster(BaseModel):
    lat: float
    lon: float
    count: int
    key: str


class GeoAggregationResponse(BaseModel):
    clusters: list[GeoCluster]
```

- [ ] **Step 3: Commit**

```bash
git add be/models.py
git commit -m "feat: add sample and geo aggregation models"
```

---

### Task 2: Backend — Update data_portal models in models.py

**Files:**
- Modify: `be/models.py`

- [ ] **Step 1: Update DataPortal DataSource — remove samples, add new fields**

In `be/models.py`, replace the existing `data_portal` DataSource definition:

```python
# DataPortal.
data_portal = DataSource(
    name="DataPortal",
    fields=[
        FieldDefinition(name="taxId", type=int),
        FieldDefinition(name="scientificName", type=str),
        FieldDefinition(name="commonName", type=str),
        FieldDefinition(name="phylogeny", type=dict[str, str]),
        FieldDefinition(name="currentStatus", type=str),
        FieldDefinition(name="currentStatusOrder", type=int),
        FieldDefinition(name="bioSamplesStatus", type=str, filterable=True),
        FieldDefinition(name="rawDataStatus", type=str, filterable=True),
        FieldDefinition(name="assembliesStatus", type=str, filterable=True),
        FieldDefinition(name="rawData", type=list[dict[str, str | None]]),
        FieldDefinition(name="assemblies", type=list[dict[str, str | None]]),
        FieldDefinition(name="sampleCount", type=int),
        FieldDefinition(name="locations", type=list[dict[str, float]]),
        FieldDefinition(name="countries", type=list[str], filterable=True),
    ],
    default_sort_field="currentStatusOrder",
    default_sort_order="desc",
)
```

Note: `samples` field removed, `sampleCount`, `locations`, `countries` added. `countries` is filterable.

- [ ] **Step 2: Add BoundsFilterMixin for reuse across search params**

Add above the DataSource class in `be/models.py`:

```python
class BoundsFilterMixin(BaseModel):
    """Mixin for geo bounding box filtering on data_portal via cross-index query."""
    top_left_lat: float | None = Field(None, description="Bounding box top-left latitude")
    top_left_lon: float | None = Field(None, description="Bounding box top-left longitude")
    bottom_right_lat: float | None = Field(None, description="Bounding box bottom-right latitude")
    bottom_right_lon: float | None = Field(None, description="Bounding box bottom-right longitude")

    def has_bounds(self) -> bool:
        return all(
            v is not None
            for v in [self.top_left_lat, self.top_left_lon, self.bottom_right_lat, self.bottom_right_lon]
        )


class TaxonomyFilterMixin(BaseModel):
    """Mixin for taxonomy filters on data_portal."""
    kingdom: str | None = Field(None, description="Filter by kingdom")
    tax_order: str | None = Field(None, description="Filter by order")
    family: str | None = Field(None, description="Filter by family")
```

- [ ] **Step 3: Manually extend DataPortalSearchParams with bounds and taxonomy**

After the `data_portal.generate_classes()` call, add:

```python
(DataPortalData, DataPortalAggregationResponse, DataPortalSearchParams) = (
    data_portal.generate_classes()
)


# Extend DataPortalSearchParams with bounds and taxonomy filters.
class DataPortalSearchParamsExtended(DataPortalSearchParams, BoundsFilterMixin, TaxonomyFilterMixin):
    pass


# Override the name for use in main.py.
DataPortalSearchParams = DataPortalSearchParamsExtended
```

- [ ] **Step 4: Commit**

```bash
git add be/models.py
git commit -m "feat: update data_portal models with sampleCount, locations, countries, taxonomy/bounds filters"
```

---

### Task 3: Backend — Add sample search and detail endpoints

**Files:**
- Modify: `be/main.py`

- [ ] **Step 1: Add imports for new models**

Update the import block in `be/main.py`:

```python
from models import (
    get_list_of_aggregations,
    ElasticResponse,
    ElasticDetailsResponse,
    DataPortalData,
    DataPortalSearchParams,
    DataPortalAggregationResponse,
    SampleData,
    SampleSearchParams,
    SampleAggregationResponse,
    GeoAggregationParams,
    GeoCluster,
    GeoAggregationResponse,
)
```

- [ ] **Step 2: Add GET /samples search endpoint**

Add below the existing data_portal endpoints in `be/main.py`:

```python
# Samples


@app.get("/samples")
async def samples_search(
    params: Annotated[SampleSearchParams, Query()],
) -> ElasticResponse[SampleData, SampleAggregationResponse]:
    return await elastic_search(
        index_name="samples",
        params=params,
        data_class=SampleData,
        aggregation_class=SampleAggregationResponse,
    )
```

- [ ] **Step 3: Add GET /samples/geo_aggregation endpoint**

This must be defined **before** `/samples/{accession}` to avoid FastAPI treating `geo_aggregation` as an accession value. Add in `be/main.py`:

```python
@app.get("/samples/geo_aggregation")
async def samples_geo_aggregation(
    params: Annotated[GeoAggregationParams, Query()],
) -> GeoAggregationResponse:
    # Map zoom level to geotile_grid precision (zoom 0-4 → precision 4, zoom 5-8 → precision 6, etc.)
    precision = min(max(params.zoom + 2, 4), 12)

    search_body = {
        "size": 0,
        "aggs": {
            "grid": {
                "geotile_grid": {
                    "field": "location",
                    "precision": precision,
                },
                "aggs": {
                    "centroid": {
                        "geo_centroid": {"field": "location"}
                    }
                },
            }
        },
    }

    # Add filters.
    filters = []
    if params.tax_id is not None:
        filters.append({"term": {"taxId": params.tax_id}})
    if params.has_bounds():
        filters.append({
            "geo_bounding_box": {
                "location": {
                    "top_left": {"lat": params.top_left_lat, "lon": params.top_left_lon},
                    "bottom_right": {"lat": params.bottom_right_lat, "lon": params.bottom_right_lon},
                }
            }
        })

    if filters:
        search_body["query"] = {"bool": {"filter": filters}}
    else:
        search_body["query"] = {"match_all": {}}

    try:
        response = await app.state.es_client.search(index="samples", body=search_body)
        buckets = response["aggregations"]["grid"]["buckets"]
        clusters = [
            GeoCluster(
                lat=bucket["centroid"]["location"]["lat"],
                lon=bucket["centroid"]["location"]["lon"],
                count=bucket["doc_count"],
                key=bucket["key"],
            )
            for bucket in buckets
        ]
        return GeoAggregationResponse(clusters=clusters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geo aggregation error: {str(e)}")
```

- [ ] **Step 4: Add GET /samples/{accession} detail endpoint**

Add after the geo_aggregation endpoint in `be/main.py`:

```python
@app.get("/samples/{accession}")
async def sample_details(
    accession: Annotated[str, Path(description="BioSamples accession")],
) -> ElasticDetailsResponse[SampleData]:
    return await elastic_details(
        index_name="samples",
        record_id=accession,
        data_class=SampleData,
    )
```

- [ ] **Step 5: Verify the server starts**

Run: `cd be && python -c "from main import app; print('OK')"`
Expected: `OK` (no import errors)

- [ ] **Step 6: Commit**

```bash
git add be/main.py
git commit -m "feat: add sample search, geo aggregation, and sample detail endpoints"
```

---

### Task 4: Backend — Update data_portal endpoint with taxonomy aggs and bounds filtering

**Files:**
- Modify: `be/main.py`

- [ ] **Step 1: Modify elastic_search to accept additional_aggs and additional_filters**

In `be/main.py`, update the `elastic_search` function signature and body:

```python
async def elastic_search(index_name, params, data_class, aggregation_class,
                          additional_aggs=None, additional_filters=None):
    # Build the query body based on whether there is full text search.
    if params.q:
        query_body = {"multi_match": {"query": params.q, "fields": ["*"]}}
    else:
        query_body = {"match_all": {}}

    # Adding filters.
    filters = []
    aggregation_fields = get_list_of_aggregations(aggregation_class)
    if aggregation_fields:
        for aggregation_field in aggregation_fields:
            filter_value = getattr(params, aggregation_field)
            if filter_value:
                filters.append({"terms": {aggregation_field: [filter_value]}})

    # Add any additional filters passed by the caller.
    if additional_filters:
        filters.extend(additional_filters)

    # Combine query with filters.
    search_body = {
        "from": params.start,
        "size": params.size,
        "query": {
            "bool": {
                "must": query_body,
                "filter": filters,
            }
        },
        "aggs": defaultdict(dict),
    }

    # Adding aggregation fields.
    if aggregation_fields:
        for aggregation_field in aggregation_fields:
            search_body["aggs"][aggregation_field] = {
                "terms": {"field": aggregation_field}
            }

    # Add any additional aggregations passed by the caller.
    if additional_aggs:
        search_body["aggs"].update(additional_aggs)

    # Adding sort field and sort order
    search_body["sort"] = [{params.sort_field: {"order": params.sort_order}}]

    # Performing the search.
    try:
        # Execute the async search request.
        response = await app.state.es_client.search(index=index_name, body=search_body)
        # Extract total count and hits.
        total = response["hits"]["total"]["value"]
        hits = [r["_source"] for r in response["hits"]["hits"]]
        aggregations = response["aggregations"]
        # Return the results.
        return ElasticResponse[data_class, aggregation_class](
            total=total,
            start=params.start,
            size=params.size,
            results=hits,
            aggregations=aggregations,
        )

    except Exception as e:
        # Handle Elasticsearch errors.
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
```

- [ ] **Step 2: Update the data_portal_search endpoint to add taxonomy aggs and bounds filtering**

Replace the existing `data_portal_search` function in `be/main.py`:

```python
@app.get("/data_portal")
async def data_portal_search(
    params: Annotated[DataPortalSearchParams, Query()],
) -> ElasticResponse[DataPortalData, DataPortalAggregationResponse]:
    # Taxonomy aggregations (nested field paths not supported by DataSource pattern).
    additional_aggs = {
        "kingdom": {"terms": {"field": "phylogeny.kingdom.keyword"}},
        "tax_order": {"terms": {"field": "phylogeny.order.keyword"}},
        "family": {"terms": {"field": "phylogeny.family.keyword"}},
    }

    # Taxonomy filters.
    additional_filters = []
    if params.kingdom:
        additional_filters.append({"term": {"phylogeny.kingdom.keyword": params.kingdom}})
    if params.tax_order:
        additional_filters.append({"term": {"phylogeny.order.keyword": params.tax_order}})
    if params.family:
        additional_filters.append({"term": {"phylogeny.family.keyword": params.family}})

    # Geo bounds cross-index filtering: find taxIds with samples in the bounding box.
    if params.has_bounds():
        bounds_response = await app.state.es_client.search(
            index="samples",
            body={
                "size": 0,
                "query": {
                    "geo_bounding_box": {
                        "location": {
                            "top_left": {"lat": params.top_left_lat, "lon": params.top_left_lon},
                            "bottom_right": {"lat": params.bottom_right_lat, "lon": params.bottom_right_lon},
                        }
                    }
                },
                "aggs": {
                    "tax_ids": {
                        "terms": {"field": "taxId", "size": 10000}
                    }
                },
            },
        )
        tax_ids = [
            bucket["key"]
            for bucket in bounds_response["aggregations"]["tax_ids"]["buckets"]
        ]
        if tax_ids:
            additional_filters.append({"terms": {"taxId": tax_ids}})
        else:
            # No samples in bounds — return empty results.
            additional_filters.append({"term": {"taxId": -1}})

    return await elastic_search(
        index_name="data_portal",
        params=params,
        data_class=DataPortalData,
        aggregation_class=DataPortalAggregationResponse,
        additional_aggs=additional_aggs,
        additional_filters=additional_filters,
    )
```

- [ ] **Step 3: Verify the server starts**

Run: `cd be && python -c "from main import app; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add be/main.py
git commit -m "feat: add taxonomy aggregations and geo bounds filtering to data_portal endpoint"
```

---

### Task 5: Backend — Test infrastructure and backend tests

**Files:**
- Create: `be/tests/__init__.py`
- Create: `be/tests/conftest.py`
- Create: `be/tests/test_models.py`
- Create: `be/tests/test_endpoints.py`
- Create: `be/requirements-dev.txt`

- [ ] **Step 1: Create requirements-dev.txt**

Create `be/requirements-dev.txt`:

```
-r requirements.txt
pytest>=8.0.0
httpx>=0.27.0
```

- [ ] **Step 2: Install dev dependencies**

Run: `cd be && pip install -r requirements-dev.txt`

- [ ] **Step 3: Create test package and conftest**

Create `be/tests/__init__.py` (empty file).

Create `be/tests/conftest.py`:

```python
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
def mock_es_client():
    """Create a mock AsyncElasticsearch client."""
    client = AsyncMock()
    return client


@pytest.fixture
async def client(mock_es_client):
    """Create a test client with mocked ES."""
    app.state.es_client = mock_es_client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 4: Create model tests**

Create `be/tests/test_models.py`:

```python
from models import (
    DataPortalData,
    DataPortalSearchParams,
    SampleData,
    SampleSearchParams,
    GeoAggregationParams,
    GeoCluster,
    GeoAggregationResponse,
    get_list_of_aggregations,
    SampleAggregationResponse,
    DataPortalAggregationResponse,
)


def test_data_portal_data_has_sample_count():
    """DataPortalData should have sampleCount, locations, countries — not samples."""
    fields = DataPortalData.__annotations__
    assert "sampleCount" in fields
    assert "locations" in fields
    assert "countries" in fields
    assert "samples" not in fields


def test_data_portal_search_params_has_taxonomy_and_bounds():
    """DataPortalSearchParams should have taxonomy and bounds filter fields."""
    params = DataPortalSearchParams(kingdom="Plantae", tax_order="Poales", family="Poaceae")
    assert params.kingdom == "Plantae"
    assert params.tax_order == "Poales"
    assert params.family == "Poaceae"
    assert params.has_bounds() is False

    params_with_bounds = DataPortalSearchParams(
        top_left_lat=52.0, top_left_lon=-1.0,
        bottom_right_lat=50.0, bottom_right_lon=1.0,
    )
    assert params_with_bounds.has_bounds() is True


def test_sample_data_fields():
    """SampleData should have all sample-level fields."""
    fields = SampleData.__annotations__
    for field_name in ["accession", "taxId", "scientificName", "location",
                       "country", "derivedFrom", "trackingSystem"]:
        assert field_name in fields, f"Missing field: {field_name}"


def test_sample_aggregation_fields():
    """SampleAggregationResponse should have aggregations for filterable fields."""
    agg_fields = get_list_of_aggregations(SampleAggregationResponse)
    assert "country" in agg_fields
    assert "collectingInstitution" in agg_fields
    assert "sex" in agg_fields
    assert "organismPart" in agg_fields
    assert "taxId" in agg_fields


def test_data_portal_aggregation_fields():
    """DataPortalAggregationResponse should include countries aggregation."""
    agg_fields = get_list_of_aggregations(DataPortalAggregationResponse)
    assert "countries" in agg_fields
    assert "bioSamplesStatus" in agg_fields


def test_geo_aggregation_params_bounds():
    """GeoAggregationParams.has_bounds should check all four coords."""
    params = GeoAggregationParams(zoom=5)
    assert params.has_bounds() is False

    params = GeoAggregationParams(
        zoom=5, top_left_lat=52.0, top_left_lon=-1.0,
        bottom_right_lat=50.0, bottom_right_lon=1.0,
    )
    assert params.has_bounds() is True


def test_geo_cluster_model():
    """GeoCluster should hold lat, lon, count, key."""
    cluster = GeoCluster(lat=51.43, lon=-0.31, count=24, key="12/2047/1362")
    assert cluster.count == 24


def test_geo_aggregation_response():
    """GeoAggregationResponse should hold a list of clusters."""
    resp = GeoAggregationResponse(clusters=[
        GeoCluster(lat=51.43, lon=-0.31, count=24, key="12/2047/1362"),
    ])
    assert len(resp.clusters) == 1
```

- [ ] **Step 5: Create endpoint tests**

Create `be/tests/test_endpoints.py`:

```python
import pytest


@pytest.mark.anyio
async def test_samples_search(client, mock_es_client):
    """GET /samples should return search results from samples index."""
    mock_es_client.search.return_value = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_source": {
                        "accession": "SAMEA7522340",
                        "taxId": 43171,
                        "scientificName": "Linaria vulgaris",
                        "commonName": "common toadflax",
                        "location": {"lat": 51.4282, "lon": -0.3121},
                        "country": "United Kingdom",
                        "locality": "Surrey",
                        "habitat": "riparian",
                        "elevation": 8.0,
                        "collectionDate": "2020-09-01",
                        "collectedBy": "M. Christenhusz",
                        "collectingInstitution": "RBG Kew",
                        "sex": "hermaphrodite",
                        "organismPart": "flower",
                        "lifestage": "vegetative",
                        "tolid": "daLinVulg1",
                        "derivedFrom": "SAMEA7522288",
                        "trackingSystem": "Submitted to BioSamples",
                        "projectName": "DTOL",
                    }
                }
            ],
        },
        "aggregations": {
            "collectingInstitution": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "country": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "organismPart": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "sex": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "taxId": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
        },
    }

    resp = await client.get("/samples", params={"start": 0, "size": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["results"][0]["accession"] == "SAMEA7522340"
    mock_es_client.search.assert_called_once()
    call_kwargs = mock_es_client.search.call_args
    assert call_kwargs.kwargs["index"] == "samples"


@pytest.mark.anyio
async def test_sample_detail(client, mock_es_client):
    """GET /samples/{accession} should return sample details."""
    mock_es_client.search.return_value = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_source": {
                        "accession": "SAMEA7522340",
                        "taxId": 43171,
                        "scientificName": "Linaria vulgaris",
                        "commonName": "common toadflax",
                        "location": {"lat": 51.4282, "lon": -0.3121},
                        "country": "United Kingdom",
                        "locality": None,
                        "habitat": None,
                        "elevation": None,
                        "collectionDate": None,
                        "collectedBy": None,
                        "collectingInstitution": None,
                        "sex": None,
                        "organismPart": "flower",
                        "lifestage": None,
                        "tolid": None,
                        "derivedFrom": "SAMEA7522288",
                        "trackingSystem": "Submitted to BioSamples",
                        "projectName": None,
                    }
                }
            ],
        },
    }

    resp = await client.get("/samples/SAMEA7522340")
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["derivedFrom"] == "SAMEA7522288"


@pytest.mark.anyio
async def test_geo_aggregation(client, mock_es_client):
    """GET /samples/geo_aggregation should return clustered locations."""
    mock_es_client.search.return_value = {
        "aggregations": {
            "grid": {
                "buckets": [
                    {
                        "key": "12/2047/1362",
                        "doc_count": 24,
                        "centroid": {
                            "location": {"lat": 51.43, "lon": -0.31},
                            "count": 24,
                        },
                    }
                ]
            }
        }
    }

    resp = await client.get("/samples/geo_aggregation", params={"zoom": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["clusters"]) == 1
    assert data["clusters"][0]["count"] == 24
    assert data["clusters"][0]["lat"] == 51.43


@pytest.mark.anyio
async def test_geo_aggregation_with_bounds(client, mock_es_client):
    """GET /samples/geo_aggregation with bounds should add geo_bounding_box filter."""
    mock_es_client.search.return_value = {
        "aggregations": {"grid": {"buckets": []}}
    }

    resp = await client.get("/samples/geo_aggregation", params={
        "zoom": 8,
        "top_left_lat": 52.0, "top_left_lon": -1.0,
        "bottom_right_lat": 50.0, "bottom_right_lon": 1.0,
    })
    assert resp.status_code == 200

    call_kwargs = mock_es_client.search.call_args
    body = call_kwargs.kwargs["body"]
    assert "geo_bounding_box" in str(body["query"])


@pytest.mark.anyio
async def test_data_portal_with_taxonomy_filters(client, mock_es_client):
    """GET /data_portal with kingdom filter should include taxonomy filter."""
    mock_es_client.search.return_value = {
        "hits": {"total": {"value": 0}, "hits": []},
        "aggregations": {
            "assembliesStatus": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "bioSamplesStatus": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "countries": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "rawDataStatus": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "kingdom": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "tax_order": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
            "family": {"doc_count_error_upper_bound": 0, "sum_other_doc_count": 0, "buckets": []},
        },
    }

    resp = await client.get("/data_portal", params={"kingdom": "Plantae"})
    assert resp.status_code == 200

    call_kwargs = mock_es_client.search.call_args
    body = call_kwargs.kwargs["body"]
    filters = body["query"]["bool"]["filter"]
    taxonomy_filter = [f for f in filters if "term" in f and "phylogeny.kingdom.keyword" in f.get("term", {})]
    assert len(taxonomy_filter) == 1
```

- [ ] **Step 6: Run tests**

Run: `cd be && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add be/tests/ be/requirements-dev.txt
git commit -m "test: add backend test infrastructure and tests for sample/geo endpoints"
```

---

### Task 6: Frontend — Add dash-leaflet dependency

**Files:**
- Modify: `fe/requirements.txt`

- [ ] **Step 1: Add dash-leaflet to requirements**

Add `dash-leaflet>=1.0.15` to `fe/requirements.txt` so it reads:

```
dash>=3.4.0
dash-bootstrap-components[pandas]>=1.6.0
gunicorn>=23.0.0
dash-leaflet>=1.0.15
```

- [ ] **Step 2: Install and verify**

Run: `cd fe && pip install -r requirements.txt`
Run: `cd fe && python -c "import dash_leaflet; print(dash_leaflet.__version__)"`
Expected: version number printed, no errors

- [ ] **Step 3: Commit**

```bash
git add fe/requirements.txt
git commit -m "feat: add dash-leaflet dependency for map components"
```

---

### Task 7: Frontend — New sample detail page

**Files:**
- Create: `fe/pages/sample_details.py`

- [ ] **Step 1: Create the sample detail page**

Create `fe/pages/sample_details.py`:

```python
import dash
from dash import html, callback, Output, Input
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import requests

from .data_portal import return_badge_status

BACKEND_URL = "https://aegis-be-1091670130981.europe-west2.run.app"

dash.register_page(
    __name__,
    path_template="/data-portal/<tax_id>/samples/<accession>",
    title="Sample Details - AEGIS",
)


def metadata_card(title, items):
    """Create a metadata card with label-value pairs."""
    return html.Div(
        [
            html.Div(
                title,
                style={
                    "fontSize": "0.65rem",
                    "color": "var(--aegis-text-muted)",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.05em",
                    "marginBottom": "0.5rem",
                },
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                f"{label}: ",
                                style={"color": "var(--aegis-text-muted)"},
                            ),
                            html.Span(
                                value,
                                style={
                                    "color": "var(--aegis-text-primary)",
                                    "fontFamily": "var(--font-mono)"
                                    if label in ("Lat", "Lon", "TOL ID")
                                    else "inherit",
                                },
                            ),
                        ],
                        style={"fontSize": "0.85rem", "marginBottom": "0.3rem"},
                    )
                    for label, value in items
                    if value
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "0.4rem",
                },
            ),
        ],
        style={
            "background": "var(--aegis-bg-elevated)",
            "borderRadius": "var(--radius-md)",
            "padding": "0.75rem",
            "marginBottom": "0.75rem",
        },
    )


def layout(tax_id=None, accession=None, **kwargs):
    return dbc.Container(
        [
            # Breadcrumb
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            html.A(
                                "Data Portal",
                                href="/data-portal",
                                style={
                                    "color": "var(--aegis-text-muted)",
                                    "textDecoration": "none",
                                    "fontSize": "0.8rem",
                                },
                            ),
                            html.Span(
                                " → ",
                                style={
                                    "color": "var(--aegis-text-muted)",
                                    "margin": "0 0.3rem",
                                    "fontSize": "0.8rem",
                                },
                            ),
                            html.A(
                                id="breadcrumb-species",
                                href=f"/data-portal/{tax_id}",
                                style={
                                    "color": "var(--aegis-text-muted)",
                                    "textDecoration": "none",
                                    "fontStyle": "italic",
                                    "fontSize": "0.8rem",
                                },
                            ),
                            html.Span(
                                " → ",
                                style={
                                    "color": "var(--aegis-text-muted)",
                                    "margin": "0 0.3rem",
                                    "fontSize": "0.8rem",
                                },
                            ),
                            html.Span(
                                accession,
                                style={
                                    "color": "var(--aegis-text-secondary)",
                                    "fontSize": "0.8rem",
                                },
                            ),
                        ],
                        className="pt-4 pb-3",
                    ),
                ),
            ),
            # Main content
            dbc.Row(
                dbc.Col(
                    dbc.Spinner(
                        html.Div(id="sample-detail-content", **{"data-accession": accession, "data-tax-id": tax_id}),
                        color="warning",
                    ),
                    md={"width": 10, "offset": 1},
                ),
            ),
        ],
    )


@callback(
    Output("sample-detail-content", "children"),
    Output("breadcrumb-species", "children"),
    Input("sample-detail-content", "data-accession"),
    Input("sample-detail-content", "data-tax-id"),
)
def load_sample_detail(accession, tax_id):
    """Fetch and render sample detail."""
    response = requests.get(
        f"{BACKEND_URL}/samples/{accession}",
        timeout=30,
    ).json()

    if not response.get("results"):
        return html.Div(
            [
                html.H4("Sample not found", style={"color": "var(--aegis-text-secondary)"}),
                html.P(f"No sample found with accession {accession}", style={"color": "var(--aegis-text-muted)"}),
            ],
            className="text-center py-5",
        ), accession

    sample = response["results"][0]

    # Header
    header = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                sample["accession"],
                                style={
                                    "fontFamily": "var(--font-mono)",
                                    "fontSize": "1.3rem",
                                    "color": "var(--aegis-accent-primary)",
                                },
                            ),
                            html.Div(
                                [
                                    html.Span(
                                        sample.get("scientificName", ""),
                                        style={
                                            "fontStyle": "italic",
                                            "color": "var(--aegis-text-muted)",
                                            "fontSize": "0.9rem",
                                        },
                                    ),
                                    html.Span(
                                        f" · {sample['organismPart']}" if sample.get("organismPart") else "",
                                        style={"color": "var(--aegis-text-muted)", "fontSize": "0.9rem"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                    return_badge_status(sample.get("trackingSystem", "")),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "start",
                    "marginBottom": "0.5rem",
                },
            ),
        ],
    )

    # Derived from link
    derived_from = html.Div()
    if sample.get("derivedFrom"):
        derived_from = html.Div(
            [
                html.Span("Derived from ", style={"color": "var(--aegis-text-muted)", "fontSize": "0.8rem"}),
                html.A(
                    sample["derivedFrom"],
                    href=f"/data-portal/{tax_id}/samples/{sample['derivedFrom']}",
                    style={
                        "color": "var(--aegis-accent-primary)",
                        "fontFamily": "var(--font-mono)",
                        "fontSize": "0.8rem",
                        "textDecoration": "none",
                    },
                ),
            ],
            style={"marginBottom": "1rem"},
        )

    # Metadata cards
    collection_items = [
        ("Date", sample.get("collectionDate")),
        ("By", sample.get("collectedBy")),
        ("Institution", sample.get("collectingInstitution")),
        ("Project", sample.get("projectName")),
    ]

    specimen_items = [
        ("Part", sample.get("organismPart")),
        ("Sex", sample.get("sex")),
        ("Lifestage", sample.get("lifestage")),
        ("TOL ID", sample.get("tolid")),
    ]

    location = sample.get("location")
    location_items = [
        ("Country", sample.get("country")),
        ("Locality", sample.get("locality")),
        ("Habitat", sample.get("habitat")),
        ("Elevation", f"{sample['elevation']}m" if sample.get("elevation") else None),
        ("Lat", str(location["lat"]) if location else None),
        ("Lon", str(location["lon"]) if location else None),
    ]

    # Map
    map_component = html.Div(
        "No location data available",
        style={
            "background": "var(--aegis-bg-elevated)",
            "borderRadius": "var(--radius-md)",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "minHeight": "300px",
            "color": "var(--aegis-text-muted)",
        },
    )
    if location:
        map_component = dl.Map(
            [
                dl.TileLayer(),
                dl.Marker(position=[location["lat"], location["lon"]]),
            ],
            center=[location["lat"], location["lon"]],
            zoom=12,
            style={
                "height": "300px",
                "borderRadius": "var(--radius-md)",
                "border": "1px solid var(--aegis-border-subtle)",
            },
        )

    # External links
    external_links = html.Div(
        [
            html.Span("External: ", style={"color": "var(--aegis-text-muted)"}),
            html.A(
                "BioSamples",
                href=f"https://www.ebi.ac.uk/biosamples/samples/{sample['accession']}",
                target="_blank",
                style={"color": "var(--aegis-accent-primary)", "textDecoration": "none", "marginRight": "1rem"},
            ),
            html.A(
                "ENA",
                href=f"https://www.ebi.ac.uk/ena/browser/view/{sample['accession']}",
                target="_blank",
                style={"color": "var(--aegis-accent-primary)", "textDecoration": "none"},
            ),
        ],
        style={
            "marginTop": "1rem",
            "padding": "0.75rem",
            "background": "var(--aegis-bg-elevated)",
            "border": "1px solid var(--aegis-border-subtle)",
            "borderRadius": "var(--radius-md)",
            "fontSize": "0.85rem",
        },
    )

    content = dbc.Card(
        dbc.CardBody(
            [
                header,
                derived_from,
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                metadata_card("Collection", collection_items),
                                metadata_card("Specimen", specimen_items),
                                metadata_card("Location", location_items),
                            ],
                            md=6,
                        ),
                        dbc.Col(map_component, md=6),
                    ],
                ),
                external_links,
            ],
        ),
        style={
            "background": "var(--aegis-bg-card)",
            "border": "1px solid var(--aegis-border-subtle)",
            "marginBottom": "2rem",
        },
    )

    breadcrumb_species = sample.get("scientificName", "Species")
    return content, breadcrumb_species
```

- [ ] **Step 2: Verify page loads without errors**

Run: `cd fe && python -c "import pages.sample_details; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add fe/pages/sample_details.py
git commit -m "feat: add sample detail page with metadata cards, map, and breadcrumb navigation"
```

---

### Task 8: Frontend — Update species detail page with map and hierarchical samples

**Files:**
- Modify: `fe/pages/data_portal_details.py`

- [ ] **Step 1: Add dash-leaflet import**

Add to the imports at the top of `fe/pages/data_portal_details.py`:

```python
import dash_leaflet as dl
```

- [ ] **Step 2: Add BACKEND_URL constant**

Add below the imports:

```python
BACKEND_URL = "https://aegis-be-1091670130981.europe-west2.run.app"
```

And replace all hardcoded backend URLs in the file with `BACKEND_URL`.

- [ ] **Step 3: Add helper function to build hierarchical sample list**

Add this function to `fe/pages/data_portal_details.py`:

```python
def build_sample_hierarchy(samples, tax_id):
    """Group samples by derivedFrom to build parent-child hierarchy."""
    # Separate root samples (no parent) from derived samples.
    roots = [s for s in samples if not s.get("derivedFrom")]
    children_map = {}
    for s in samples:
        parent = s.get("derivedFrom")
        if parent:
            children_map.setdefault(parent, []).append(s)

    # If no roots found but there are samples, treat all as roots (data may lack derivedFrom).
    if not roots and samples:
        roots = samples

    elements = []
    for root in roots:
        accession = root["accession"]
        # Root sample row.
        elements.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.A(
                                accession,
                                href=f"/data-portal/{tax_id}/samples/{accession}",
                                style={
                                    "color": "var(--aegis-accent-primary)",
                                    "fontFamily": "var(--font-mono)",
                                    "fontSize": "0.8rem",
                                    "textDecoration": "none",
                                },
                            ),
                            html.Span(
                                f" · {root.get('organismPart', '')}",
                                style={"color": "var(--aegis-text-muted)", "fontSize": "0.8rem"},
                            ) if root.get("organismPart") else None,
                            html.Span(
                                f" · {root.get('country', '')}",
                                style={"color": "var(--aegis-text-muted)", "fontSize": "0.8rem"},
                            ) if root.get("country") else None,
                        ],
                    ),
                    return_badge_status(root.get("trackingSystem", ""))
                    if root.get("trackingSystem")
                    else html.Span(),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "padding": "0.5rem",
                    "background": "rgba(255,255,255,0.03)",
                    "borderRadius": "4px",
                    "marginBottom": "0.3rem",
                },
            )
        )
        # Children (indented).
        children = children_map.get(accession, [])
        if children:
            child_elements = []
            for child in children:
                child_acc = child["accession"]
                child_elements.append(
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.A(
                                        child_acc,
                                        href=f"/data-portal/{tax_id}/samples/{child_acc}",
                                        style={
                                            "color": "var(--aegis-accent-primary)",
                                            "fontFamily": "var(--font-mono)",
                                            "fontSize": "0.8rem",
                                            "textDecoration": "none",
                                        },
                                    ),
                                    html.Span(
                                        f" · {child.get('organismPart', '')}",
                                        style={"color": "var(--aegis-text-muted)", "fontSize": "0.8rem"},
                                    ) if child.get("organismPart") else None,
                                ],
                            ),
                            return_badge_status(child.get("trackingSystem", ""))
                            if child.get("trackingSystem")
                            else html.Span(),
                        ],
                        style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                            "padding": "0.4rem 0.5rem",
                            "borderBottom": "1px solid rgba(255,255,255,0.03)",
                        },
                    )
                )
            elements.append(
                html.Div(
                    child_elements,
                    style={
                        "marginLeft": "1.5rem",
                        "borderLeft": "2px solid var(--aegis-border-subtle)",
                        "paddingLeft": "0.75rem",
                        "marginBottom": "0.5rem",
                    },
                )
            )

    return html.Div(elements) if elements else html.P(
        "No samples available", style={"color": "var(--aegis-text-muted)"}
    )
```

- [ ] **Step 4: Update create_data_portal_record callback to include species map and fetch samples**

Replace the `create_data_portal_record` callback to:
1. Add map in the summary card (right column alongside info grid)
2. Fetch samples from the samples API
3. Store samples data in intermediate-value

Key changes inside the callback:
- After building `info_grid` and `taxonomy_path`, add a map:

```python
    # Fetch samples for this species from the samples API.
    samples_response = requests.get(
        f"{BACKEND_URL}/samples",
        params={"taxId": tax_id, "size": 1000},
        timeout=30,
    ).json()
    samples_list = samples_response.get("results", [])

    # Build map from sample locations.
    markers = []
    for s in samples_list:
        loc = s.get("location")
        if loc and loc.get("lat") and loc.get("lon"):
            markers.append(
                dl.Marker(
                    position=[loc["lat"], loc["lon"]],
                    children=dl.Tooltip(f"{s['accession']} · {s.get('organismPart', '')}"),
                )
            )

    if markers:
        species_map = dl.Map(
            [dl.TileLayer()] + markers,
            center=[markers[0].position[0], markers[0].position[1]] if len(markers) == 1 else [0, 0],
            zoom=6,
            bounds=[[m.position[0], m.position[1]] for m in markers] if len(markers) > 1 else None,
            style={
                "height": "200px",
                "borderRadius": "var(--radius-md)",
                "border": "1px solid var(--aegis-border-subtle)",
            },
        )
    else:
        species_map = html.Div()
```

Reorganize the summary card to use two columns: left for info_grid + taxonomy, right for map.

- [ ] **Step 5: Update create_tabs callback — replace metadata tab with hierarchical samples**

In the `create_tabs` callback, replace the metadata_tab branch to use `build_sample_hierarchy`:

```python
    if active_tab == "metadata_tab":
        samples = json.loads(agg_data).get("samples", [])
        hierarchy = build_sample_hierarchy(samples, tax_id)
        # ... return hierarchy with pagination hidden
```

Note: The `tax_id` needs to be passed to the callback. Add it to the intermediate-value store along with samples data:

```python
agg_data = {
    "tax_id": tax_id,
    "samples": samples_list,
    "rawData": response.get("rawData", []),
    "assemblies": response.get("assemblies", []),
}
```

- [ ] **Step 6: Verify the page loads**

Run: `cd fe && python -c "import pages.data_portal_details; print('OK')"`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add fe/pages/data_portal_details.py
git commit -m "feat: add map and hierarchical sample display to species detail page"
```

---

### Task 9: Frontend — Update data portal list page with map and enhanced facets

**Files:**
- Modify: `fe/pages/data_portal.py`

- [ ] **Step 1: Add imports**

Add to the top of `fe/pages/data_portal.py`:

```python
import dash_leaflet as dl
from dash import dcc
```

Add BACKEND_URL constant:

```python
BACKEND_URL = "https://aegis-be-1091670130981.europe-west2.run.app"
```

Replace the hardcoded backend URL in the callback with `BACKEND_URL`.

- [ ] **Step 2: Add map component to the layout**

In the layout, between the search input and the status legend, add:

```python
# Map
html.Div(
    dl.Map(
        [
            dl.TileLayer(),
            dl.GeoJSON(id="map-clusters", options={"pointToLayer": None}),
        ],
        id="sample-map",
        center=[30, 0],
        zoom=2,
        style={
            "height": "250px",
            "borderRadius": "var(--radius-md)",
            "border": "1px solid var(--aegis-border-subtle)",
            "marginBottom": "1rem",
        },
    ),
    id="map-container",
),
# Store for map bounds
dcc.Store(id="map-bounds"),
```

- [ ] **Step 3: Add taxonomy and country filter sections to the sidebar**

In the filter sidebar (dbc.CardBody), add new filter sections after the existing "Data Status" checklist:

```python
# Taxonomy filters
html.Div(
    "Taxonomy",
    style={
        "fontSize": "0.8rem",
        "fontWeight": "600",
        "color": "var(--aegis-text-secondary)",
        "marginBottom": "0.75rem",
        "marginTop": "1rem",
    },
),
dbc.Checklist(id="kingdom_filter"),
html.Div(
    "Order",
    style={
        "fontSize": "0.8rem",
        "fontWeight": "600",
        "color": "var(--aegis-text-secondary)",
        "marginBottom": "0.75rem",
        "marginTop": "0.75rem",
    },
),
dbc.Checklist(id="order_filter"),
html.Div(
    "Family",
    style={
        "fontSize": "0.8rem",
        "fontWeight": "600",
        "color": "var(--aegis-text-secondary)",
        "marginBottom": "0.75rem",
        "marginTop": "0.75rem",
    },
),
dbc.Checklist(id="family_filter"),
html.Div(
    "Country",
    style={
        "fontSize": "0.8rem",
        "fontWeight": "600",
        "color": "var(--aegis-text-secondary)",
        "marginBottom": "0.75rem",
        "marginTop": "1rem",
    },
),
dbc.Checklist(id="country_filter"),
```

- [ ] **Step 4: Update the main callback to handle new filters and populate new checklists**

Update the `create_update_data_table` callback signature to include new filter inputs and outputs:

```python
@callback(
    Output("data_table", "children"),
    Output("checklist_input", "options"),
    Output("pagination", "max_value"),
    Output("kingdom_filter", "options"),
    Output("order_filter", "options"),
    Output("family_filter", "options"),
    Output("country_filter", "options"),
    Input("checklist_input", "value"),
    Input("input", "value"),
    Input("pagination", "active_page"),
    Input("kingdom_filter", "value"),
    Input("order_filter", "value"),
    Input("family_filter", "value"),
    Input("country_filter", "value"),
    Input("map-bounds", "data"),
    running=[
        (Output("input", "class_name"), "invisible", "visible"),
        (Output("pagination", "class_name"), "invisible", "justify-content-end"),
        (Output("filters-card", "class_name"), "invisible", "card-title"),
    ],
)
def create_update_data_table(
    filter_values, input_value, active_page,
    kingdom_values, order_values, family_values, country_values,
    map_bounds,
):
```

Inside the callback, add taxonomy/country/bounds params to the API request:

```python
    # Taxonomy filters.
    if kingdom_values:
        params["kingdom"] = kingdom_values[0] if isinstance(kingdom_values, list) else kingdom_values
    if order_values:
        params["tax_order"] = order_values[0] if isinstance(order_values, list) else order_values
    if family_values:
        params["family"] = family_values[0] if isinstance(family_values, list) else family_values
    if country_values:
        params["countries"] = country_values[0] if isinstance(country_values, list) else country_values

    # Map bounds filtering.
    if map_bounds:
        params["top_left_lat"] = map_bounds["top_left_lat"]
        params["top_left_lon"] = map_bounds["top_left_lon"]
        params["bottom_right_lat"] = map_bounds["bottom_right_lat"]
        params["bottom_right_lon"] = map_bounds["bottom_right_lon"]
```

Add `sampleCount` column to the table header and body:

```python
    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th(v)
                    for v in ["Scientific Name", "Common Name", "Samples", "Current Status"]
                ]
            )
        )
    ]
```

In the table body, add the sampleCount cell:

```python
    html.Td(
        row.get("sampleCount", 0),
        style={"color": "var(--aegis-text-secondary)"},
    ),
```

Build taxonomy and country checklist options from aggregations:

```python
    # Taxonomy checklist options from aggregations.
    kingdom_options = [
        {"label": f"{b['key']} ({b['doc_count']})", "value": b["key"]}
        for b in response.get("aggregations", {}).get("kingdom", {}).get("buckets", [])
    ]
    order_options = [
        {"label": f"{b['key']} ({b['doc_count']})", "value": b["key"]}
        for b in response.get("aggregations", {}).get("tax_order", {}).get("buckets", [])
    ]
    family_options = [
        {"label": f"{b['key']} ({b['doc_count']})", "value": b["key"]}
        for b in response.get("aggregations", {}).get("family", {}).get("buckets", [])
    ]
    country_options = [
        {"label": f"{b['key']} ({b['doc_count']})", "value": b["key"]}
        for b in response.get("aggregations", {}).get("countries", {}).get("buckets", [])
    ]
```

Update the return to include new outputs:

```python
    return table_container, options, max_pages, kingdom_options, order_options, family_options, country_options
```

Also update the empty-state return to include empty lists for the new outputs:

```python
    return empty_state, [], 1, [], [], [], []
```

- [ ] **Step 5: Add map cluster callback**

Add a new callback to fetch and render geo clusters on map viewport changes. This uses a clientside callback for the map bounds and a server callback for fetching clusters:

```python
@callback(
    Output("map-clusters", "data"),
    Input("sample-map", "bounds"),
    Input("sample-map", "zoom"),
)
def update_map_clusters(bounds, zoom):
    """Fetch geo-aggregated clusters for the current map viewport."""
    if not bounds or not zoom:
        return {"type": "FeatureCollection", "features": []}

    params = {"zoom": zoom}
    if bounds:
        params["top_left_lat"] = bounds[1][0]
        params["top_left_lon"] = bounds[0][1]
        params["bottom_right_lat"] = bounds[0][0]
        params["bottom_right_lon"] = bounds[1][1]

    try:
        response = requests.get(
            f"{BACKEND_URL}/samples/geo_aggregation",
            params=params,
            timeout=15,
        ).json()
    except Exception:
        return {"type": "FeatureCollection", "features": []}

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [c["lon"], c["lat"]]},
            "properties": {"count": c["count"], "key": c["key"]},
        }
        for c in response.get("clusters", [])
    ]
    return {"type": "FeatureCollection", "features": features}
```

- [ ] **Step 6: Verify the page loads**

Run: `cd fe && python -c "import pages.data_portal; print('OK')"`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add fe/pages/data_portal.py
git commit -m "feat: add project-level map and taxonomy/country facets to data portal list page"
```

---

### Task 10: End-to-end verification

- [ ] **Step 1: Run backend tests**

Run: `cd be && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Verify backend starts without errors**

Run: `cd be && python -c "from main import app; print('Endpoints:', [r.path for r in app.routes])"`
Expected: Prints list including `/data_portal`, `/samples`, `/samples/geo_aggregation`, `/samples/{accession}`

- [ ] **Step 3: Verify frontend starts without errors**

Run: `cd fe && python -c "import app; print('Pages:', list(dash.page_registry.keys()))"`
Expected: Prints list including `pages.data_portal`, `pages.data_portal_details`, `pages.sample_details`

- [ ] **Step 4: Commit any remaining fixes**

```bash
git add -A
git commit -m "chore: final verification and cleanup"
```
