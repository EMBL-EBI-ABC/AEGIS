# AEGIS Portal: Maps, Facets, and Sample Detail Page

**Date:** 2026-03-31
**Status:** Approved

## Overview

Enhance the AEGIS data portal with geographic map views at three levels (project, species, sample), additional search facets (taxonomy, country), a new sample detail page, and sample hierarchy display. Requires a new Elasticsearch index for samples and backend/frontend changes.

## Elasticsearch Changes

### Index Strategy: Two Indices

Split from one index into two:

- **`data_portal`** (species-level, one doc per taxId) — powers the species list page
- **`samples`** (sample-level, one doc per BioSamples accession) — powers maps, sample detail, and geographic search

### `data_portal` Index Mapping Changes

Remove the `samples` nested object (moved to its own index). Add:

| Field | Type | Purpose |
|-------|------|---------|
| `sampleCount` | `integer` | Display count without cross-index query |
| `locations` | `geo_point` (array) | Denormalized from samples; species-level map pins and project-level map aggregation |
| `countries` | `keyword` (array) | Denormalized from samples; country facet on list page |

Existing fields remain unchanged. The `rawData` and `assemblies` nested objects stay in this index.

New aggregation fields to wire up (already in mapping with `.keyword` sub-fields, just not used as aggregations):
- `phylogeny.kingdom.keyword`
- `phylogeny.order.keyword`
- `phylogeny.family.keyword`
- `countries`

### New `samples` Index Mapping

```json
{
  "mappings": {
    "dynamic": "strict",
    "date_detection": false,
    "properties": {
      "accession":              { "type": "keyword" },
      "taxId":                  { "type": "long" },
      "scientificName":         { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "commonName":             { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "location":               { "type": "geo_point" },
      "country":                { "type": "keyword" },
      "locality":               { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "habitat":                { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "elevation":              { "type": "float" },
      "collectionDate":         { "type": "date" },
      "collectedBy":            { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "collectingInstitution":  { "type": "keyword" },
      "sex":                    { "type": "keyword" },
      "organismPart":           { "type": "keyword" },
      "lifestage":              { "type": "keyword" },
      "tolid":                  { "type": "keyword" },
      "derivedFrom":            { "type": "keyword" },
      "trackingSystem":         { "type": "keyword" },
      "projectName":            { "type": "keyword" }
    }
  },
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "max_result_window": 100000,
    "analysis": {
      "filter": {
        "autocomplete_filter": {
          "type": "edge_ngram",
          "min_gram": 1,
          "max_gram": 20,
          "token_chars": ["letter", "digit", "whitespace"]
        }
      },
      "normalizer": {
        "lower_case_normalizer": {
          "type": "custom",
          "filter": ["lowercase"]
        }
      },
      "analyzer": {
        "autocomplete": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "autocomplete_filter"]
        }
      }
    }
  }
}
```

Key design decisions:
- `accession` as keyword (used as doc `_id`)
- `location` as `geo_point` — enables `geo_bounding_box` queries and `geotile_grid` aggregation
- `derivedFrom` as keyword — stores parent sample accession, null for root samples
- `country`, `sex`, `organismPart`, `lifestage`, `collectingInstitution`, `projectName` as keyword — facet-ready
- Settings mirror existing index (same analyzer/normalizer setup)

## Backend API Changes

### Modified Endpoints

**`GET /data_portal`**
- Add aggregation fields: `phylogeny.kingdom.keyword`, `phylogeny.order.keyword`, `phylogeny.family.keyword`, `countries`
- Add optional `bounds` parameter (top_left_lat, top_left_lon, bottom_right_lat, bottom_right_lon) for map-based filtering. When provided: query `samples` index with `geo_bounding_box` to get matching taxIds, then add taxId filter to the species query.
- Response no longer includes `samples` array; includes `sampleCount`, `locations`, `countries` instead.

**`GET /data_portal/{record_id}`**
- Response updated to reflect mapping changes (no `samples`, has `sampleCount`, `locations`, `countries`).

### New Endpoints

**`GET /samples`**
Search the samples index. Query parameters:
- `taxId` (optional) — filter by species
- `bounds` (optional) — `geo_bounding_box` filter (top_left_lat, top_left_lon, bottom_right_lat, bottom_right_lon)
- `q` (optional) — full text search
- `start`, `size` — pagination
- `sort_field`, `sort_order` — sorting
- Filter params for facets: `country`, `organismPart`, `collectingInstitution`

Returns: list of samples + aggregations (country, organismPart, collectingInstitution).

**`GET /samples/{accession}`**
Single sample detail by BioSamples accession.

**`GET /samples/geo_aggregation`**
Returns clustered sample locations for map rendering. Query parameters:
- `bounds` (optional) — viewport bounding box
- `zoom` (required) — current map zoom level, determines `geotile_grid` precision
- `taxId` (optional) — filter to one species (for species-level map)

Uses ES `geotile_grid` aggregation with `geo_centroid` sub-aggregation. Returns array of clusters:
```json
{
  "clusters": [
    { "lat": 51.43, "lon": -0.31, "count": 24, "key": "12/2047/1362" },
    { "lat": 48.85, "lon": 2.35, "count": 8, "key": "12/2074/1409" }
  ]
}
```

This single endpoint powers all three map levels:
- Project-level map: no taxId, shows all samples
- Species-level map: with taxId
- Precision scales with zoom level automatically

### Models (`models.py`)

- New `SampleData` Pydantic model matching samples index fields
- New `SampleSearchParams` extending `SearchParams` with `taxId`, bounding box fields, facet filters
- New `GeoAggregationParams` with `bounds`, `zoom`, `taxId`
- New `GeoCluster` and `GeoAggregationResponse` models
- Update `DataPortalData`: remove `samples` field, add `sampleCount` (int), `locations` (list), `countries` (list[str])
- Update `DataPortalAggregationResponse`: add kingdom, order, family, countries aggregations
- Update `DataPortalSearchParams`: add bounding box fields, taxonomy/country filter params

## Frontend Changes

### New Dependency

Add `dash-leaflet` to `fe/requirements.txt`.

### Data Portal List Page (`data_portal.py`)

**Map component:**
- `dl.MapContainer` with `dl.TileLayer` + `dl.GeoJSON` for cluster markers
- Positioned between search bar and table
- On viewport change (zoom/pan), calls `GET /samples/geo_aggregation` with current bounds + zoom
- Cluster markers show sample count; clicking a cluster zooms in
- Draw/select region on map adds `bounds` param to species search, filtering the table

**Enhanced filter sidebar:**
- Existing: pipeline status filters (bioSamplesStatus, rawDataStatus, assembliesStatus)
- New section: Taxonomy (kingdom, order, family checklists populated from aggregations)
- New section: Country (checklist populated from `countries` aggregation)

**Table changes:**
- Add "Samples" column showing `sampleCount`

### Species Detail Page (`data_portal_details.py`)

**Map in summary card:**
- Map displayed alongside the info grid (right side)
- Fetches sample locations from `GET /samples?taxId=X` (not the denormalized `locations` field, because markers need accession info for click-through)
- Markers are clickable — navigate to sample detail page
- Auto-fits bounds to show all markers

**Hierarchical samples tab:**
- Fetch samples from `GET /samples?taxId=X` instead of from species doc
- Group samples by `derivedFrom`: root samples (derivedFrom=null) at top level, derived samples indented below their parent
- Visual: left border line connecting children to parent
- Each accession is a clickable link to `/data-portal/<tax_id>/samples/<accession>`
- Show: accession, organismPart, sex, country, status

**Info grid additions:**
- Sample count
- Countries list

### New Sample Detail Page (`sample_details.py`)

**Route:** `/data-portal/<tax_id>/samples/<accession>`

**Breadcrumb:** Data Portal → *Scientific Name* → ACCESSION

**Layout (two columns):**

Left column — metadata cards:
- **Collection:** collectionDate, collectedBy, collectingInstitution, projectName
- **Specimen:** organismPart, sex, lifestage, tolid
- **Location:** country, locality, habitat, elevation, lat, lon

Right column — map:
- Zoomed to exact `location` coordinates
- Single marker at collection site

**Additional elements:**
- `derivedFrom` link to parent sample (if not null)
- External links: BioSamples page, ENA browser
- Status badge

## Bug Fix: `trackingSystem` showing "YOUR-BUCKET-NAME"

This is a data ingestion issue, not a portal code bug. The `trackingSystem` field in existing sample data contains placeholder text "YOUR-BUCKET-NAME" instead of proper status values. The fix belongs in the ingestion pipeline (in the `biodiversity-data-ingestion` repo): compute status from actual data presence (has BioSamples accession → "Submitted to BioSamples", has raw data → "Raw Data - Submitted", has assemblies → "Assemblies - Submitted"). No portal code change needed — the badge rendering logic already handles the correct status strings.

## Scalability: Project-Level Map with Thousands of Samples

The `geotile_grid` aggregation handles this natively. It groups samples into grid cells at the current zoom level and returns a centroid + count per cell. The frontend renders these as numbered cluster markers. As the user zooms in, grid precision increases and clusters split. This approach handles tens of thousands of points efficiently — the number of clusters returned is bounded by the grid, not by the number of samples.

## Navigation Flow

```
/data-portal                              (species list + project map)
    │
    ├── click species row
    ▼
/data-portal/<tax_id>                     (species detail + species map + sample hierarchy)
    │
    ├── click sample accession
    ▼
/data-portal/<tax_id>/samples/<accession> (sample detail + collection site map)
```

## Out of Scope

- Ingestion pipeline changes (separate repo: `biodiversity-data-ingestion`)
- Re-indexing existing data into new mapping
- Annotation status tracking
- Raw data index (can be split out later if needed)
