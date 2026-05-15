import os
import urllib.parse
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException, Query, Path
from elasticsearch import AsyncElasticsearch
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from typing import Annotated

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize AsyncElasticsearch.
    es_client = AsyncElasticsearch(
        [os.getenv("ES_URL")],
        http_auth=(os.getenv("ES_USERNAME"), os.getenv("ES_PASSWORD")),
        verify_certs=True,
    )
    # Pass the client to the app's state so it's accessible in routes.
    app.state.es_client = es_client
    yield
    # Clean up by closing the Elasticsearch client.
    await es_client.close()


# Initialize FastAPI with lifespan manager.
# Served behind a proxy at https://portal.aegisearth.bio/api/* (proxy does not strip
# the prefix), so docs and routes live under /api.
app = FastAPI(
    lifespan=lifespan,
    title="AEGIS Data Portal API",
    version="0.0.1",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

api = APIRouter(prefix="/api")

# Allow all origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)


# Generic search methods.


async def elastic_search(
    index_name, params, data_class, aggregation_class,
    additional_aggs=None, additional_filters=None,
):
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
                if isinstance(filter_value, list):
                    filters.append({"terms": {aggregation_field: filter_value}})
                else:
                    filters.append({"terms": {aggregation_field: [filter_value]}})

    # Append any additional filters.
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

    # Merge any additional aggregations.
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


async def elastic_details(index_name, record_id, data_class):
    try:
        response = await app.state.es_client.search(
            index=index_name, q=f"_id:{urllib.parse.quote(record_id)}"
        )
        hits = [r["_source"] for r in response["hits"]["hits"]]
        return ElasticDetailsResponse[data_class](results=hits)
    except Exception as e:
        # Handle Elasticsearch errors.
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


# Data Portal


@api.get("/data_portal")
async def data_portal_search(
    params: Annotated[DataPortalSearchParams, Query()],
) -> ElasticResponse[DataPortalData, DataPortalAggregationResponse]:
    # Taxonomy aggregations.
    additional_aggs = {
        "kingdom": {"terms": {"field": "phylogeny.kingdom.keyword"}},
        "tax_order": {"terms": {"field": "phylogeny.order.keyword"}},
        "family": {"terms": {"field": "phylogeny.family.keyword"}},
    }

    # Taxonomy filters.
    additional_filters = []
    if params.kingdom:
        additional_filters.append(
            {"terms": {"phylogeny.kingdom.keyword": [params.kingdom]}}
        )
    if params.tax_order:
        additional_filters.append(
            {"terms": {"phylogeny.order.keyword": [params.tax_order]}}
        )
    if params.family:
        additional_filters.append(
            {"terms": {"phylogeny.family.keyword": [params.family]}}
        )

    # Geo bounds cross-index filtering.
    if params.has_bounds():
        geo_query = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": {
                        "geo_bounding_box": {
                            "location": {
                                "top_left": {
                                    "lat": params.top_left_lat,
                                    "lon": params.top_left_lon,
                                },
                                "bottom_right": {
                                    "lat": params.bottom_right_lat,
                                    "lon": params.bottom_right_lon,
                                },
                            }
                        }
                    }
                }
            },
            "aggs": {
                "tax_ids": {
                    "terms": {"field": "taxId", "size": 10000}
                }
            },
        }
        geo_response = await app.state.es_client.search(
            index="2026-05-15_samples", body=geo_query
        )
        tax_ids = [
            bucket["key"]
            for bucket in geo_response["aggregations"]["tax_ids"]["buckets"]
        ]
        if tax_ids:
            additional_filters.append({"terms": {"taxId": tax_ids}})
        else:
            # No samples in bounds — return empty results by filtering on impossible value.
            additional_filters.append({"terms": {"taxId": [-1]}})

    return await elastic_search(
        index_name="2026-05-15_data_portal",
        params=params,
        data_class=DataPortalData,
        aggregation_class=DataPortalAggregationResponse,
        additional_aggs=additional_aggs,
        additional_filters=additional_filters if additional_filters else None,
    )


@api.get("/data_portal/{record_id}")
async def data_portal_details(
    record_id: Annotated[str, Path(description="Record ID")],
) -> ElasticDetailsResponse[DataPortalData]:
    return await elastic_details(
        index_name="2026-05-15_data_portal",
        record_id=record_id,
        data_class=DataPortalData,
    )


# Samples


@api.get("/samples")
async def samples_search(
    params: Annotated[SampleSearchParams, Query()],
) -> ElasticResponse[SampleData, SampleAggregationResponse]:
    return await elastic_search(
        index_name="2026-05-15_samples",
        params=params,
        data_class=SampleData,
        aggregation_class=SampleAggregationResponse,
    )


@api.get("/samples/geo_aggregation")
async def samples_geo_aggregation(
    params: Annotated[GeoAggregationParams, Query()],
) -> GeoAggregationResponse:
    precision = min(max(params.zoom + 2, 4), 12)

    # Build filters.
    filters = []
    must = []
    if params.has_bounds():
        filters.append(
            {
                "geo_bounding_box": {
                    "location": {
                        "top_left": {
                            "lat": params.top_left_lat,
                            "lon": params.top_left_lon,
                        },
                        "bottom_right": {
                            "lat": params.bottom_right_lat,
                            "lon": params.bottom_right_lon,
                        },
                    }
                }
            }
        )
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

    # Build query.
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

    try:
        response = await app.state.es_client.search(
            index="2026-05-15_samples", body=search_body
        )
        clusters = [
            GeoCluster(
                lat=bucket["centroid"]["location"]["lat"],
                lon=bucket["centroid"]["location"]["lon"],
                count=bucket["doc_count"],
                key=bucket["key"],
            )
            for bucket in response["aggregations"]["grid"]["buckets"]
        ]
        return GeoAggregationResponse(clusters=clusters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geo aggregation error: {str(e)}")


@api.get("/samples/{accession}")
async def samples_details(
    accession: Annotated[str, Path(description="Sample accession")],
) -> ElasticDetailsResponse[SampleData]:
    return await elastic_details(
        index_name="2026-05-15_samples",
        record_id=accession,
        data_class=SampleData,
    )


app.include_router(api)
