import pytest
from unittest.mock import AsyncMock


SAMPLE_AGGREGATIONS = {
    "collectingInstitution": {
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0,
        "buckets": [],
    },
    "country": {
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0,
        "buckets": [],
    },
    "organismPart": {
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0,
        "buckets": [],
    },
    "sex": {
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0,
        "buckets": [],
    },
    "taxId": {
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0,
        "buckets": [],
    },
}

DATA_PORTAL_AGGREGATIONS = {
    "assembliesStatus": {
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0,
        "buckets": [],
    },
    "bioSamplesStatus": {
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0,
        "buckets": [],
    },
    "countries": {
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0,
        "buckets": [],
    },
    "rawDataStatus": {
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0,
        "buckets": [],
    },
    "kingdom": {
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0,
        "buckets": [],
    },
    "tax_order": {
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0,
        "buckets": [],
    },
    "family": {
        "doc_count_error_upper_bound": 0,
        "sum_other_doc_count": 0,
        "buckets": [],
    },
}

SAMPLE_HIT = {
    "accession": "SAMEA7522340",
    "taxId": 6344,
    "scientificName": "Hirudo medicinalis",
    "commonName": "medicinal leech",
    "location": {"lat": 51.5, "lon": -0.1},
    "country": "United Kingdom",
    "locality": None,
    "habitat": None,
    "elevation": None,
    "collectionDate": None,
    "collectedBy": None,
    "collectingInstitution": None,
    "sex": None,
    "organismPart": None,
    "lifestage": None,
    "tolid": None,
    "derivedFrom": "SAMEA7522339",
    "trackingSystem": "COPO",
    "projectName": None,
}


@pytest.mark.anyio
async def test_samples_search(client, mock_es_client):
    """Mock ES response, call GET /samples, verify response structure and index name."""
    mock_es_client.search.return_value = {
        "hits": {
            "total": {"value": 1},
            "hits": [{"_source": SAMPLE_HIT}],
        },
        "aggregations": SAMPLE_AGGREGATIONS,
    }

    response = await client.get("/api/samples")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["accession"] == "SAMEA7522340"
    assert "aggregations" in data

    # Verify ES was called with the correct index.
    call_kwargs = mock_es_client.search.call_args
    assert call_kwargs.kwargs["index"] == "2026-05-15_samples"


@pytest.mark.anyio
async def test_sample_detail(client, mock_es_client):
    """Mock ES, call GET /samples/SAMEA7522340, verify derivedFrom in response."""
    mock_es_client.search.return_value = {
        "hits": {
            "total": {"value": 1},
            "hits": [{"_source": SAMPLE_HIT}],
        },
    }

    response = await client.get("/api/samples/SAMEA7522340")
    assert response.status_code == 200

    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["derivedFrom"] == "SAMEA7522339"


@pytest.mark.anyio
async def test_geo_aggregation(client, mock_es_client):
    """Mock ES with grid buckets, call GET /samples/geo_aggregation?zoom=5, verify clusters."""
    mock_es_client.search.return_value = {
        "aggregations": {
            "grid": {
                "buckets": [
                    {
                        "key": "5/16/10",
                        "doc_count": 42,
                        "centroid": {
                            "location": {"lat": 51.5, "lon": -0.1},
                            "count": 42,
                        },
                    },
                    {
                        "key": "5/16/11",
                        "doc_count": 7,
                        "centroid": {
                            "location": {"lat": 48.8, "lon": 2.3},
                            "count": 7,
                        },
                    },
                ]
            }
        }
    }

    response = await client.get("/api/samples/geo_aggregation?zoom=5")
    assert response.status_code == 200

    data = response.json()
    assert len(data["clusters"]) == 2
    assert data["clusters"][0]["count"] == 42
    assert data["clusters"][0]["lat"] == 51.5
    assert data["clusters"][1]["key"] == "5/16/11"


@pytest.mark.anyio
async def test_geo_aggregation_with_bounds(client, mock_es_client):
    """Verify geo_bounding_box appears in ES query when bounds are provided."""
    mock_es_client.search.return_value = {
        "aggregations": {
            "grid": {
                "buckets": []
            }
        }
    }

    response = await client.get(
        "/api/samples/geo_aggregation"
        "?zoom=5"
        "&top_left_lat=60.0&top_left_lon=-10.0"
        "&bottom_right_lat=50.0&bottom_right_lon=10.0"
    )
    assert response.status_code == 200

    # Inspect the body sent to ES.
    call_kwargs = mock_es_client.search.call_args
    body = call_kwargs.kwargs["body"]
    query_filters = body["query"]["bool"]["filter"]
    geo_filter = query_filters[0]
    assert "geo_bounding_box" in geo_filter
    bbox = geo_filter["geo_bounding_box"]["location"]
    assert bbox["top_left"]["lat"] == 60.0
    assert bbox["bottom_right"]["lon"] == 10.0


@pytest.mark.anyio
async def test_data_portal_with_taxonomy_filters(client, mock_es_client):
    """Verify taxonomy filter appears in ES query body when kingdom=Plantae."""
    mock_es_client.search.return_value = {
        "hits": {
            "total": {"value": 0},
            "hits": [],
        },
        "aggregations": DATA_PORTAL_AGGREGATIONS,
    }

    response = await client.get("/api/data_portal?kingdom=Plantae")
    assert response.status_code == 200

    # Inspect the ES query body for the taxonomy filter.
    call_kwargs = mock_es_client.search.call_args
    body = call_kwargs.kwargs["body"]
    filters = body["query"]["bool"]["filter"]
    kingdom_filters = [
        f for f in filters
        if "terms" in f and "phylogeny.kingdom.keyword" in f["terms"]
    ]
    assert len(kingdom_filters) == 1
    assert kingdom_filters[0]["terms"]["phylogeny.kingdom.keyword"] == ["Plantae"]
