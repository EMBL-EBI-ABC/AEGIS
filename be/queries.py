# be/queries.py
import urllib.parse
from collections import defaultdict

from models import (
    get_list_of_aggregations,
    ElasticResponse,
    ElasticDetailsResponse,
    GeoCluster,
    GeoAggregationResponse,
)

DATA_PORTAL_INDEX = "2026-05-15_data_portal"
SAMPLES_INDEX = "2026-05-15_samples"


class QueryError(RuntimeError):
    """Raised when an Elasticsearch query fails. Transport-agnostic."""
    pass


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
        raise QueryError(f"Search error: {str(e)}") from e


async def elastic_details(*, es_client, index_name: str, record_id: str, data_class):
    try:
        response = await es_client.search(
            index=index_name, q=f"_id:{urllib.parse.quote(record_id, safe='')}"
        )
        hits = [r["_source"] for r in response["hits"]["hits"]]
        return ElasticDetailsResponse[data_class](results=hits)
    except Exception as e:
        raise QueryError(f"Search error: {str(e)}") from e


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
        raise QueryError(f"Geo aggregation error: {str(e)}") from e
