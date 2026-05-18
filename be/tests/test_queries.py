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
