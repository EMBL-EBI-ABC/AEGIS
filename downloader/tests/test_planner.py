import json
from pathlib import Path

import httpx

from aegis_downloader.api_client import ApiClient
from aegis_downloader.planner import build_plan
from tests.conftest import make_mock_client_factory


FIXTURES = Path(__file__).parent / "fixtures"


def _load_record() -> dict:
    return json.loads((FIXTURES / "data_portal_43171.json").read_text())


def _client_with_record(record: dict) -> ApiClient:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/data_portal/" in url and url.endswith(str(record["taxId"])):
            return httpx.Response(200, json={"results": [record]})
        if "/data_portal" in url:
            return httpx.Response(200, json={
                "total": 1, "start": 0, "size": 100,
                "results": [record], "aggregations": {},
            })
        if "/samples" in url:
            return httpx.Response(200, json={
                "total": 0, "start": 0, "size": 1000, "results": [], "aggregations": {},
            })
        raise AssertionError(f"unexpected URL {url}")
    return ApiClient("http://test", transport=make_mock_client_factory(handler))


def test_build_plan_with_all_types_produces_tasks_for_each_extractor():
    record = _load_record()
    client = _client_with_record(record)
    plan = build_plan(
        client=client,
        types={"raw-data", "assemblies", "annotations", "samples-metadata"},
        server_filters={},
        explicit_tax_ids=None,
    )
    data_types_seen = {t.data_type for t in plan.tasks}
    assert data_types_seen == {"raw-data", "assemblies", "annotations"}
    # 2 raw fastq + 2 assemblies + 3 annotations
    assert plan.total_tasks == 7
