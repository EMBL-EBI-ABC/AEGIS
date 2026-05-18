import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, FastAPI, Query, Path, Request
from fastapi.responses import JSONResponse
from elasticsearch import AsyncElasticsearch
from fastapi.middleware.cors import CORSMiddleware

from models import (
    ElasticResponse, ElasticDetailsResponse,
    DataPortalData, DataPortalSearchParams, DataPortalAggregationResponse,
    SampleData, SampleSearchParams, SampleAggregationResponse,
    GeoAggregationParams, GeoAggregationResponse,
)
from queries import (
    QueryError,
    DATA_PORTAL_INDEX, SAMPLES_INDEX,
    elastic_search, elastic_details,
    data_portal_search_full, samples_geo_aggregation_query,
)
from mcp_server import build_mcp_app, set_es_client


mcp_app = build_mcp_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastMCP's Streamable HTTP app has its own session-manager lifespan.
    # Nest it inside ours so both run at startup/shutdown.
    async with mcp_app.router.lifespan_context(app):
        es_client = AsyncElasticsearch(
            [os.getenv("ES_URL")],
            http_auth=(os.getenv("ES_USERNAME"), os.getenv("ES_PASSWORD")),
            verify_certs=True,
        )
        app.state.es_client = es_client
        set_es_client(es_client)
        try:
            yield
        finally:
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
    license_info={"name": "Apache 2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0.html"},
)
api = APIRouter(prefix="/api")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(QueryError)
async def query_error_handler(request: Request, exc: QueryError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@api.get("/data_portal")
async def data_portal_search(
    params: Annotated[DataPortalSearchParams, Query()],
) -> ElasticResponse[DataPortalData, DataPortalAggregationResponse]:
    return await data_portal_search_full(
        es_client=app.state.es_client,
        params=params,
        samples_index=SAMPLES_INDEX,
        data_portal_index=DATA_PORTAL_INDEX,
        data_class=DataPortalData,
        aggregation_class=DataPortalAggregationResponse,
    )


@api.get("/data_portal/{record_id}")
async def data_portal_details(
    record_id: Annotated[str, Path(description="Record ID")],
) -> ElasticDetailsResponse[DataPortalData]:
    return await elastic_details(
        es_client=app.state.es_client,
        index_name=DATA_PORTAL_INDEX,
        record_id=record_id,
        data_class=DataPortalData,
    )


@api.get("/samples")
async def samples_search(
    params: Annotated[SampleSearchParams, Query()],
) -> ElasticResponse[SampleData, SampleAggregationResponse]:
    return await elastic_search(
        es_client=app.state.es_client,
        index_name=SAMPLES_INDEX,
        params=params,
        data_class=SampleData,
        aggregation_class=SampleAggregationResponse,
    )


@api.get("/samples/geo_aggregation")
async def samples_geo_aggregation(
    params: Annotated[GeoAggregationParams, Query()],
) -> GeoAggregationResponse:
    return await samples_geo_aggregation_query(
        es_client=app.state.es_client,
        params=params,
        samples_index=SAMPLES_INDEX,
    )


@api.get("/samples/{accession}")
async def samples_details(
    accession: Annotated[str, Path(description="Sample accession")],
) -> ElasticDetailsResponse[SampleData]:
    return await elastic_details(
        es_client=app.state.es_client,
        index_name=SAMPLES_INDEX,
        record_id=accession,
        data_class=SampleData,
    )


app.include_router(api)
app.mount("/api/mcp", mcp_app)
