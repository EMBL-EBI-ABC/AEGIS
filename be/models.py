from pydantic import BaseModel, Field, create_model
from typing import Generic, Literal, TypeVar

T = TypeVar("T")  # Datasource data type
A = TypeVar("A")  # Datasource aggregation type


# Generic aggregation classes.


class AggregationBucket(BaseModel):
    key: int | str
    doc_count: int


class Aggregation(BaseModel):
    doc_count_error_upper_bound: int
    sum_other_doc_count: int
    buckets: list[AggregationBucket]


def get_list_of_aggregations(aggregation_class):
    return sorted(aggregation_class.schema()["properties"].keys())


# Generic Elastic response classes.


class ElasticResponse(BaseModel, Generic[T, A]):
    total: int
    start: int
    size: int
    results: list[T]
    aggregations: dict


class ElasticDetailsResponse(BaseModel, Generic[T]):
    results: list[T]


# Base Elastic query class.


class SearchParams(BaseModel):
    model_config = {
        "populate_by_name": True,
        "extra": "forbid",
    }
    # Basic query parameters.
    q: str | None = Field(None, description="Search query string")
    start: int = Field(0, description="Starting point of the results")
    size: int = Field(10, gt=0, description="Number of results per page")
    # No sorting by default, child classes can override this.
    sort_field: str | None = None
    sort_order: Literal["desc", "asc"] = "asc"


# Datasource definition.


class FieldDefinition:
    def __init__(self, name: str, type: type, filterable: bool = False):
        self.name = name
        self.type = type
        self.filterable = filterable


class DataSource:
    def __init__(
        self,
        name: str,
        fields: list[FieldDefinition],
        default_sort_field: str,
        default_sort_order: Literal["desc", "asc"],
    ):
        self.name = name
        self.fields = fields
        self.default_sort_field = default_sort_field
        self.default_sort_order = default_sort_order

    def generate_classes(self):
        fields = {field.name: (field.type, field.filterable) for field in self.fields}

        # Build Data class: fields with None in their type get a default of None
        data_field_definitions = {}
        for name, (type_, _) in fields.items():
            if "None" in str(type_):
                data_field_definitions[name] = (type_, None)
            else:
                data_field_definitions[name] = (type_, ...)

        Data = create_model("Data", **data_field_definitions)

        class AggregationResponse(BaseModel):
            __annotations__ = {
                name: Aggregation
                for name, (_, filterable) in fields.items()
                if filterable
            }

        class SearchParamsExtended(SearchParams):
            # Define filterable fields with default values
            locals().update(
                {
                    name: Field(None, description=f"{name} query", alias=name)
                    for name, (type_, filterable) in fields.items()
                    if filterable
                }
            )
            __annotations__ = {
                name: type_ | None
                for name, (type_, filterable) in fields.items()
                if filterable
            }
            # Define default sort field and order.
            sort_field: str | None = Field(
                self.default_sort_field, description="Sort field"
            )
            sort_order: Literal["desc", "asc"] = Field(
                self.default_sort_order, description="Sort order"
            )

        return Data, AggregationResponse, SearchParamsExtended


# Bounds and taxonomy filter mixins.


class BoundsFilterMixin(BaseModel):
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
    kingdom: str | None = Field(None, description="Filter by kingdom")
    tax_order: str | None = Field(None, description="Filter by order")
    family: str | None = Field(None, description="Filter by family")


# DataPortal.
data_portal = DataSource(
    name="DataPortal",
    fields=[
        FieldDefinition(name="taxId", type=int),
        FieldDefinition(name="scientificName", type=str),
        FieldDefinition(name="commonName", type=str | None),
        FieldDefinition(name="phylogeny", type=dict[str, str]),
        FieldDefinition(name="currentStatus", type=str),
        FieldDefinition(name="currentStatusOrder", type=int),
        FieldDefinition(name="bioSamplesStatus", type=str, filterable=True),
        FieldDefinition(name="rawDataStatus", type=str, filterable=True),
        FieldDefinition(name="assembliesStatus", type=str, filterable=True),
        FieldDefinition(name="rawData", type=list[dict[str, str | None]]),
        FieldDefinition(name="assemblies", type=list[dict[str, str | None]]),
        FieldDefinition(name="sampleCount", type=int | None),
        FieldDefinition(name="locations", type=list[dict[str, float]] | None),
        FieldDefinition(name="countries", type=list[str] | None, filterable=True),
    ],
    default_sort_field="currentStatusOrder",
    default_sort_order="desc",
)
(DataPortalData, DataPortalAggregationResponse, DataPortalSearchParams) = (
    data_portal.generate_classes()
)


class DataPortalSearchParamsExtended(DataPortalSearchParams, BoundsFilterMixin, TaxonomyFilterMixin):
    pass

DataPortalSearchParams = DataPortalSearchParamsExtended


# Samples.
samples_source = DataSource(
    name="Samples",
    fields=[
        # Always present
        FieldDefinition(name="accession", type=str),
        FieldDefinition(name="taxId", type=int, filterable=True),
        FieldDefinition(name="scientificName", type=str),
        FieldDefinition(name="commonName", type=str | None),
        FieldDefinition(name="trackingSystem", type=str | None),
        FieldDefinition(name="projectName", type=str | None),
        # Mandatory (ERC000053)
        FieldDefinition(name="organismPart", type=str | None, filterable=True),
        FieldDefinition(name="lifestage", type=str | None),
        FieldDefinition(name="sex", type=str | None, filterable=True),
        FieldDefinition(name="collectedBy", type=str | None),
        FieldDefinition(name="collectionDate", type=str | None),
        FieldDefinition(name="locality", type=str | None),
        FieldDefinition(name="country", type=str | None, filterable=True),
        FieldDefinition(name="habitat", type=str | None),
        FieldDefinition(name="collectingInstitution", type=str | None, filterable=True),
        # Recommended
        FieldDefinition(name="location", type=dict[str, float] | None),
        FieldDefinition(name="elevation", type=float | None),
        FieldDefinition(name="tolid", type=str | None),
        FieldDefinition(name="specimenVoucher", type=str | None),
        # Relationships
        FieldDefinition(name="derivedFrom", type=str | None),
        FieldDefinition(name="sampleSymbiontOf", type=str | None),
        FieldDefinition(name="symbiont", type=str | None),
        FieldDefinition(name="relationship", type=str | None),
        FieldDefinition(name="sampleSameAs", type=str | None),
        # Collection metadata
        FieldDefinition(name="sampleCollectionMethod", type=str | None),
        FieldDefinition(name="identifiedBy", type=str | None),
        FieldDefinition(name="identifierAffiliation", type=str | None),
        FieldDefinition(name="sampleCoordinator", type=str | None),
        FieldDefinition(name="sampleCoordinatorAffiliation", type=str | None),
        FieldDefinition(name="barcodingCenter", type=str | None),
        FieldDefinition(name="gal", type=str | None),
        FieldDefinition(name="specimenId", type=str | None),
        FieldDefinition(name="galSampleId", type=str | None),
        FieldDefinition(name="proxyVoucher", type=str | None),
        FieldDefinition(name="proxyBiomaterial", type=str | None),
        FieldDefinition(name="bioMaterial", type=str | None),
        FieldDefinition(name="cultureOrStrainId", type=str | None),
        # Original location
        FieldDefinition(name="originalCollectionDate", type=str | None),
        FieldDefinition(name="originalGeographicLocation", type=str | None),
        FieldDefinition(name="originalLatitude", type=float | None),
        FieldDefinition(name="originalLongitude", type=float | None),
        # Transect/numeric
        FieldDefinition(name="latitudeStart", type=float | None),
        FieldDefinition(name="longitudeStart", type=float | None),
        FieldDefinition(name="latitudeEnd", type=float | None),
        FieldDefinition(name="longitudeEnd", type=float | None),
        FieldDefinition(name="depth", type=float | None),
        # Custom fields
        FieldDefinition(name="customFields", type=list[dict[str, str]] | None),
    ],
    default_sort_field="accession",
    default_sort_order="asc",
)
(SampleData, SampleAggregationResponse, SampleSearchParams) = (
    samples_source.generate_classes()
)


# Geo aggregation models.


class GeoAggregationParams(BaseModel):
    model_config = {"extra": "forbid"}
    zoom: int = Field(..., ge=0, le=20, description="Map zoom level")
    top_left_lat: float | None = Field(None, description="Bounding box top-left latitude")
    top_left_lon: float | None = Field(None, description="Bounding box top-left longitude")
    bottom_right_lat: float | None = Field(None, description="Bounding box bottom-right latitude")
    bottom_right_lon: float | None = Field(None, description="Bounding box bottom-right longitude")
    tax_id: int | None = Field(None, description="Filter to a specific species")
    q: str | None = Field(None, description="Full text search query")
    country: str | None = Field(None, description="Filter by country")
    trackingSystem: str | None = Field(None, description="Filter by tracking status")

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
