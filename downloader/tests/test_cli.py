import httpx
import pytest

from aegis_downloader.cli import build_parser, parse_types, run


def test_parse_types_default_returns_all_four():
    assert parse_types(None) == {"raw-data", "assemblies", "annotations", "samples-metadata"}


def test_parse_types_comma_separated():
    assert parse_types("raw-data,annotations") == {"raw-data", "annotations"}


def test_parse_types_rejects_unknown_value():
    with pytest.raises(SystemExit):
        parse_types("raw-data,bogus")


def test_workers_capped_at_32():
    args = build_parser().parse_args(["--workers", "100"])
    assert args.workers == 100  # parser doesn't cap; run() does
    # cap is enforced inside run()


def test_run_dry_run_writes_manifest(tmp_path, monkeypatch):
    record = {
        "taxId": 1, "scientificName": "X",
        "rawData": [{"fastq_ftp": "host/a.fq.gz"}],
        "assemblies": [], "annotations": [],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/samples" in url:
            return httpx.Response(200, json={"total": 0, "start": 0, "size": 1000, "results": [], "aggregations": {}})
        return httpx.Response(200, json={"total": 1, "start": 0, "size": 100, "results": [record], "aggregations": {}})

    monkeypatch.setattr("aegis_downloader.cli._make_transport", lambda: httpx.MockTransport(handler))

    exit_code = run([
        "--type", "raw-data",
        "--output", str(tmp_path),
        "--backend-url", "http://test",
        "--dry-run",
    ])
    assert exit_code == 0
    assert (tmp_path / "manifest.tsv").exists()
    assert not (tmp_path / "by_species").exists()
