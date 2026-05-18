import httpx
import pytest

from aegis_downloader.api_client import ApiClient
from tests.conftest import make_mock_client_factory


def test_iter_data_portal_paginates_until_total_reached():
    pages = {
        0: {
            "total": 3, "start": 0, "size": 2,
            "results": [{"taxId": 1}, {"taxId": 2}],
            "aggregations": {},
        },
        2: {
            "total": 3, "start": 2, "size": 2,
            "results": [{"taxId": 3}],
            "aggregations": {},
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        start = int(request.url.params.get("start", "0"))
        return httpx.Response(200, json=pages[start])

    client = ApiClient("http://test", transport=make_mock_client_factory(handler))
    records = list(client.iter_data_portal(filters={}, page_size=2))
    assert [r["taxId"] for r in records] == [1, 2, 3]


def test_iter_data_portal_handles_empty_results():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "total": 0, "start": 0, "size": 100, "results": [], "aggregations": {},
        })

    client = ApiClient("http://test", transport=make_mock_client_factory(handler))
    records = list(client.iter_data_portal(filters={}, page_size=100))
    assert records == []


def test_iter_data_portal_sends_filter_params():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={
            "total": 0, "start": 0, "size": 100, "results": [], "aggregations": {},
        })

    client = ApiClient("http://test", transport=make_mock_client_factory(handler))
    list(client.iter_data_portal(filters={"kingdom": "Animalia", "tax_order": "Lepidoptera"}, page_size=100))
    assert captured[0].url.params["kingdom"] == "Animalia"
    assert captured[0].url.params["tax_order"] == "Lepidoptera"
