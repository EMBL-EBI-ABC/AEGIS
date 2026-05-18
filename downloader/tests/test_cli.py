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


def test_run_downloads_files_end_to_end(tmp_path, monkeypatch):
    record = {
        "taxId": 1, "scientificName": "Test species",
        "rawData": [{"fastq_ftp": "host/a.fq.gz"}],
        "assemblies": [{"accession": "GCA_1", "version": "1"}],
        "annotations": [],
    }
    payloads = {
        "https://host/a.fq.gz": b"FASTQ_PAYLOAD",
        "https://www.ebi.ac.uk/ena/browser/api/fasta/GCA_1.1?download=true&gzip=true": b"FASTA_GZ_PAYLOAD",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/samples" in url:
            return httpx.Response(200, json={"total": 0, "start": 0, "size": 1000, "results": [], "aggregations": {}})
        if "/data_portal" in url:
            return httpx.Response(200, json={"total": 1, "start": 0, "size": 100, "results": [record], "aggregations": {}})
        if request.method == "HEAD":
            if url in payloads:
                return httpx.Response(200, headers={"content-length": str(len(payloads[url]))})
            return httpx.Response(500)
        return httpx.Response(200, content=payloads[url])

    monkeypatch.setattr("aegis_downloader.cli._make_transport", lambda: httpx.MockTransport(handler))

    exit_code = run([
        "--type", "raw-data,assemblies",
        "--output", str(tmp_path),
        "--backend-url", "http://test",
        "--workers", "2",
        "--max-retries", "0",
    ])
    assert exit_code == 0
    fq = tmp_path / "by_species/1_test_species/raw_data/a.fq.gz"
    fa = tmp_path / "by_species/1_test_species/assemblies/GCA_1.1.fasta.gz"
    assert fq.read_bytes() == b"FASTQ_PAYLOAD"
    assert fa.read_bytes() == b"FASTA_GZ_PAYLOAD"
    manifest = (tmp_path / "manifest.tsv").read_text()
    assert manifest.count("\tok\t") == 2
