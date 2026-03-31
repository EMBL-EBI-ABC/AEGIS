from pydantic import BaseModel, Field
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
    aggregations: A


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

        class Data(BaseModel):
            __annotations__ = {name: type for name, (type, _) in fields.items()}

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
