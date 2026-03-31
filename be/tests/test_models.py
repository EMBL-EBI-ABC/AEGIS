from models import (
    DataPortalData,
    DataPortalSearchParams,
    SampleData,
    SampleAggregationResponse,
    GeoAggregationParams,
    GeoCluster,
    GeoAggregationResponse,
    get_list_of_aggregations,
)


def test_data_portal_data_has_sample_count():
    """Verify sampleCount, locations, countries are in DataPortalData and samples is NOT."""
    fields = DataPortalData.model_fields
    assert "sampleCount" in fields
    assert "locations" in fields
    assert "countries" in fields
    assert "samples" not in fields


def test_data_portal_search_params_has_taxonomy_and_bounds():
    """Verify kingdom, tax_order, family exist and has_bounds() works."""
    params = DataPortalSearchParams(
        kingdom="Plantae",
        tax_order=None,
        family=None,
        top_left_lat=60.0,
        top_left_lon=-10.0,
        bottom_right_lat=50.0,
        bottom_right_lon=10.0,
    )
    assert params.kingdom == "Plantae"
    assert params.tax_order is None
    assert params.family is None
    assert params.has_bounds() is True

    params_no_bounds = DataPortalSearchParams()
    assert params_no_bounds.has_bounds() is False


def test_sample_data_fields():
    """Verify key fields exist in SampleData."""
    fields = SampleData.model_fields
    assert "accession" in fields
    assert "taxId" in fields
    assert "scientificName" in fields
    assert "location" in fields
    assert "country" in fields
    assert "derivedFrom" in fields
    assert "trackingSystem" in fields


def test_sample_aggregation_fields():
    """Verify filterable fields appear as aggregations."""
    agg_fields = get_list_of_aggregations(SampleAggregationResponse)
    assert "country" in agg_fields
    assert "collectingInstitution" in agg_fields
    assert "sex" in agg_fields
    assert "organismPart" in agg_fields
    assert "taxId" in agg_fields


def test_geo_aggregation_params_bounds():
    """Verify has_bounds() logic on GeoAggregationParams."""
    params_with = GeoAggregationParams(
        zoom=5,
        top_left_lat=60.0,
        top_left_lon=-10.0,
        bottom_right_lat=50.0,
        bottom_right_lon=10.0,
    )
    assert params_with.has_bounds() is True

    params_without = GeoAggregationParams(zoom=5)
    assert params_without.has_bounds() is False

    params_partial = GeoAggregationParams(zoom=5, top_left_lat=60.0)
    assert params_partial.has_bounds() is False


def test_geo_cluster_model():
    """Basic construction test for GeoCluster."""
    cluster = GeoCluster(lat=51.5, lon=-0.1, count=42, key="5/16/10")
    assert cluster.lat == 51.5
    assert cluster.lon == -0.1
    assert cluster.count == 42
    assert cluster.key == "5/16/10"


def test_geo_aggregation_response():
    """List of clusters test for GeoAggregationResponse."""
    clusters = [
        GeoCluster(lat=51.5, lon=-0.1, count=10, key="5/16/10"),
        GeoCluster(lat=48.8, lon=2.3, count=5, key="5/16/11"),
    ]
    response = GeoAggregationResponse(clusters=clusters)
    assert len(response.clusters) == 2
    assert response.clusters[0].count == 10
    assert response.clusters[1].lat == 48.8
