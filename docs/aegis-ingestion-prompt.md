# AEGIS Ingestion Pipeline — Claude Code Session Prompt

Paste everything below into a new Claude Code session in `/Users/alexey/biodiversity-data-ingestion`.

---

## Context

I'm building the ingestion pipeline for the AEGIS data portal (Ancient Environmental Genomics Initiative for Sustainability). The portal codebase lives at `/Users/alexey/AEGIS` — it's a FastAPI backend + Dash frontend that reads from Elasticsearch.

The portal expects **two ES indices**:

1. **`data_portal`** — one doc per species (keyed by `taxId`), powers the species list page
2. **`samples`** — one doc per BioSamples accession, powers maps, sample detail, and geographic search

The ingestion pipeline needs to:
1. Fetch sample metadata from BioSamples API for AEGIS project `PRJEB80366`
2. Fetch raw data (experiments) and assemblies from ENA
3. Fetch taxonomy from ENA XML API
4. Resolve parent-child sample relationships (`sample derived from` in BioSamples characteristics)
5. Build and index documents into both ES indices

## Current state of this repo

- `airflow/dags/aegis_metadata_dag.py` — started but incomplete (DAG body is `pass`)
- `airflow/dags/dependencies/aegis_projects.py` — has the project config: `PRJEB80366` with bucket `prj-ext-prod-biodiv-data-in-aegis`
- `airflow/dags/dependencies/collect_metadata_experiments_assemblies.py` — **working** function that fetches from BioSamples + ENA, joins metadata. Returns `dict[sample_id, sample_record]`
- `beam/` — existing Beam pipeline for larger biodiversity projects (DTOL, ASG, ERGA). Has `build_data_portal_record` and `process_samples_for_dwh` in `beam/src/dependencies/utils/map_functions.py` — these show the data transformation patterns but are tailored to other projects, not AEGIS

## Airflow vs Airflow + Apache Beam

For the other biodiversity projects (DTOL, ERGA) we use Apache Beam because they have hundreds of thousands of samples and the map/reduce parallelism is needed. For AEGIS, the dataset is much smaller (hundreds to low thousands of samples for a few crop species).

**Recommendation: Airflow-only for AEGIS.** Use Airflow's `@task` decorator with Python functions for each step. The pipeline is linear: fetch → transform → index. No need for Beam's distributed processing at this scale.

**Inflection point where Beam becomes worth it:**
- More than ~10,000 samples (sequential processing starts taking >30 minutes)
- Need to fan out to multiple external API calls in parallel (e.g., BioSamples + ENA + GoAT + NBN Atlas per sample)
- Need for complex cross-source joins/aggregations that benefit from Beam's CoGroupByKey
- Need for exactly-once processing guarantees with retry logic

If AEGIS grows to that scale, the transformation functions written for Airflow can be refactored into Beam DoFns — the business logic stays the same, only the execution wrapper changes.

## What I need built

Complete the AEGIS Airflow DAG with these tasks:

### Task 1: Fetch metadata (already partially done)
- Uses `collect_metadata_experiments_assemblies.main("PRJEB80366", "AEGIS", bucket_name)`
- Returns dict of raw BioSamples records joined with ENA experiments/assemblies
- Writes JSONL to GCS bucket

### Task 2: Build `samples` index documents
For each BioSamples record, extract fields into the `samples` ES index format. The field mapping from BioSamples characteristics is (see `process_samples_for_dwh` in `beam/src/dependencies/utils/map_functions.py` for reference):

| ES field | BioSamples source |
|----------|-------------------|
| `accession` | `sample["accession"]` |
| `taxId` | `sample["taxId"]` |
| `scientificName` | `sample["characteristics"]["organism"][0]["text"]` |
| `commonName` | Looked up from taxonomy or sample data |
| `location` | `{"lat": float(characteristics["geographic location (latitude)"][0]["text"]), "lon": float(characteristics["geographic location (longitude)"][0]["text"])}` — null if missing |
| `country` | `characteristics["geographic location (country and/or sea)"][0]["text"]` |
| `locality` | `characteristics["geographic location (region and locality)"][0]["text"]` |
| `habitat` | `characteristics["habitat"][0]["text"]` |
| `elevation` | Parse from characteristics if present |
| `collectionDate` | `characteristics["collection date"][0]["text"]` — format as ISO date |
| `collectedBy` | `characteristics["collected by"][0]["text"]` |
| `collectingInstitution` | `characteristics["collecting institution"][0]["text"]` |
| `sex` | `characteristics["sex"][0]["text"]` |
| `organismPart` | `characteristics["organism part"][0]["text"]` |
| `lifestage` | `characteristics["lifestage"][0]["text"]` |
| `tolid` | `characteristics["tolid"][0]["text"]` |
| `derivedFrom` | `characteristics["sample derived from"][0]["text"]` — null if not present |
| `trackingSystem` | Computed: has assemblies → "Assemblies - Submitted", has experiments → "Raw Data - Submitted", else → "Submitted to BioSamples" |
| `projectName` | `sample["project_name"]` |

All characteristic lookups should be wrapped in try/except — many fields are optional.

### Task 3: Build `data_portal` index documents
Group samples by `taxId`. For each species, build a species-level document. Reference `build_data_portal_record` in `beam/src/dependencies/utils/map_functions.py` for the general pattern. Key fields:

| ES field | Source |
|----------|--------|
| `taxId` | Group key (integer) |
| `scientificName` | From ENA taxonomy XML API |
| `commonName` | From ENA taxonomy XML or BioSamples |
| `phylogeny` | `{"kingdom": "...", "phylum": "...", "class": "...", "order": "...", "family": "...", "genus": "..."}` — from ENA XML lineage |
| `currentStatus` | Highest status across all samples: "Submitted to BioSamples" → "Raw Data - Submitted" → "Assemblies - Submitted" |
| `currentStatusOrder` | 1 for BioSamples, 2 for Raw Data, 3 for Assemblies |
| `bioSamplesStatus` | "Done" (always, if samples exist) |
| `rawDataStatus` | "Done" if any sample has experiments, else "Waiting" |
| `assembliesStatus` | "Done" if any sample has assemblies, else "Waiting" |
| `rawData` | Flattened list of all experiment records across all samples (same fields as current ENA filereport response) |
| `assemblies` | Flattened list of all assembly records across all samples |
| `sampleCount` | Number of samples for this species |
| `locations` | Array of `{"lat": ..., "lon": ...}` from all samples with coordinates |
| `countries` | Deduplicated list of country values from all samples |

### Task 4: Index into Elasticsearch
- Create indices with mappings below (or update via alias swap)
- Bulk index documents using the ES Python client
- Use index alias pattern: create `YYYY-MM-DD_data_portal` and `YYYY-MM-DD_samples`, then swap aliases `data_portal` → new index, `samples` → new index

### Task 5: Wire up the DAG
- Schedule: daily or on-demand
- Task dependencies: fetch → build_samples_docs → build_data_portal_docs → index_to_es
- (build_samples_docs and build_data_portal_docs can run in parallel if fetch output is shared via XCom or GCS)

## ES Mappings

### `data_portal` index

```json
{
  "mappings": {
    "dynamic": "strict",
    "date_detection": false,
    "properties": {
      "taxId":                { "type": "long" },
      "scientificName":       { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
      "commonName":           { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
      "phylogeny": {
        "properties": {
          "kingdom":  { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "phylum":   { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "class":    { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "order":    { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "family":   { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "genus":    { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "species":  { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } }
        }
      },
      "currentStatus":        { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
      "currentStatusOrder":   { "type": "long" },
      "bioSamplesStatus":     { "type": "keyword" },
      "rawDataStatus":        { "type": "keyword" },
      "assembliesStatus":     { "type": "keyword" },
      "rawData": {
        "properties": {
          "study_accession":      { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "sample_accession":     { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "experiment_accession": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "run_accession":        { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "fastq_ftp":            { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "instrument_platform":  { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "instrument_model":     { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "library_layout":       { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "library_strategy":     { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "library_source":       { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "library_selection":    { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "read_count":           { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "base_count":           { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "first_public":         { "type": "date" },
          "last_updated":         { "type": "date" }
        }
      },
      "assemblies": {
        "properties": {
          "accession":        { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "assembly_name":    { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "description":      { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "study_accession":  { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "sample_accession": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
          "last_updated":     { "type": "date" },
          "version":          { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } }
        }
      },
      "sampleCount":          { "type": "integer" },
      "locations":            { "type": "geo_point" },
      "countries":            { "type": "keyword" }
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

### `samples` index

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

## Known bug to fix

The `trackingSystem` field on samples currently contains "YOUR-BUCKET-NAME" in the portal. This happens because the current ingestion writes the GCS bucket name instead of computing the status. The correct logic is in `process_samples_for_dwh` in `beam/src/dependencies/utils/map_functions.py` lines 225-230:

```python
if "experiments" in sample and len(sample["experiments"]) > 0:
    trackingSystem = "Raw Data - Submitted"
elif "assemblies" in sample and len(sample["assemblies"]) > 0:
    trackingSystem = "Assemblies - Submitted"
else:
    trackingSystem = "Submitted to BioSamples"
```

## Important: BioSamples characteristics field access pattern

BioSamples returns characteristics as:
```json
{
  "characteristics": {
    "organism": [{"text": "Linaria vulgaris", "ontologyTerms": [...]}],
    "geographic location (latitude)": [{"text": "51.4282", "unit": "DD"}],
    "sample derived from": [{"text": "SAMEA7522288"}]
  }
}
```

Always access as `sample["characteristics"]["field_name"][0]["text"]` with try/except for missing fields.

## What to produce

1. A complete, working Airflow DAG in `airflow/dags/aegis_metadata_dag.py` with helper functions in `airflow/dags/dependencies/`
2. Transformation functions that build both ES index document formats
3. ES indexing logic with alias swap
4. Keep it Airflow-only (no Beam) — see reasoning above
