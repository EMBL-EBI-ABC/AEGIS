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
    # 2 raw fastq + 2 assemblies + 5 annotations
    assert plan.total_tasks == 9


def test_build_plan_type_subset_excludes_other_extractors():
    record = _load_record()
    client = _client_with_record(record)
    plan = build_plan(
        client=client,
        types={"assemblies"},
        server_filters={},
        explicit_tax_ids=None,
    )
    assert all(t.data_type == "assemblies" for t in plan.tasks)
    assert plan.total_tasks == 2


def test_build_plan_explicit_tax_id_filters_results():
    record = _load_record()
    other = {**record, "taxId": 99999, "scientificName": "Other species"}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "total": 2, "start": 0, "size": 100,
            "results": [record, other], "aggregations": {},
        })

    client = ApiClient("http://test", transport=make_mock_client_factory(handler))
    plan = build_plan(
        client=client,
        types={"raw-data"},
        server_filters={},
        explicit_tax_ids={43171},
    )
    assert {t.tax_id for t in plan.tasks} == {43171}


def test_build_plan_explicit_tax_id_empty_set_excludes_everything():
    record = _load_record()
    client = _client_with_record(record)
    plan = build_plan(
        client=client,
        types={"raw-data", "assemblies", "annotations"},
        server_filters={},
        explicit_tax_ids=set(),
    )
    assert plan.total_tasks == 0


def test_build_plan_writes_per_species_metadata_json():
    record = _load_record()
    client = _client_with_record(record)
    plan = build_plan(
        client=client,
        types={"raw-data"},
        server_filters={},
        explicit_tax_ids=None,
    )
    [metadata_write] = plan.metadata_writes
    assert str(metadata_write.dest) == "by_species/43171_linaria_vulgaris/metadata.json"
    assert json.loads(metadata_write.content)["taxId"] == 43171


def test_build_plan_writes_samples_metadata_tsv_when_requested():
    record = _load_record()
    sample = {"accession": "SAMEA7522288", "taxId": 43171, "scientificName": "Linaria vulgaris"}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/samples" in url:
            return httpx.Response(200, json={
                "total": 1, "start": 0, "size": 1000, "results": [sample], "aggregations": {},
            })
        return httpx.Response(200, json={
            "total": 1, "start": 0, "size": 100, "results": [record], "aggregations": {},
        })

    client = ApiClient("http://test", transport=make_mock_client_factory(handler))
    plan = build_plan(
        client=client,
        types={"samples-metadata"},
        server_filters={},
        explicit_tax_ids=None,
    )
    samples_writes = [w for w in plan.metadata_writes if w.dest.name == "samples_metadata.tsv"]
    assert len(samples_writes) == 1
    content = samples_writes[0].content
    header, *rows = content.strip().split("\n")
    assert "accession" in header
    assert "SAMEA7522288" in rows[0]


def test_build_plan_skips_samples_when_not_in_types():
    record = _load_record()
    client = _client_with_record(record)
    plan = build_plan(
        client=client,
        types={"raw-data"},
        server_filters={},
        explicit_tax_ids=None,
    )
    assert not any(w.dest.name == "samples_metadata.tsv" for w in plan.metadata_writes)
