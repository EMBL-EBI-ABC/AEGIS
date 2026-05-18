from pathlib import Path

import httpx
import pytest

from aegis_downloader.downloader import _download_one
from aegis_downloader.models import DownloadTask


def _task(url: str = "https://example.com/a.fq.gz", dest: str = "raw/a.fq.gz", head_supported: bool = True) -> DownloadTask:
    return DownloadTask(
        url=url,
        dest=Path(dest),
        data_type="raw-data",
        tax_id=1,
        scientific_name="X",
        head_supported=head_supported,
    )


def _client_with(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_download_one_happy_path_writes_file_and_renames_partial(tmp_path):
    payload = b"hello world" * 100  # 1100 bytes

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "HEAD":
            return httpx.Response(200, headers={"content-length": str(len(payload))})
        return httpx.Response(200, content=payload)

    task = _task()
    result = _download_one(
        task=task,
        client=_client_with(handler),
        output_root=tmp_path,
        resume=True,
        max_retries=3,
    )
    assert result.status == "ok"
    assert result.bytes_downloaded == len(payload)
    final = tmp_path / "raw/a.fq.gz"
    assert final.read_bytes() == payload
    assert not (tmp_path / "raw/a.fq.gz.partial").exists()


def test_download_one_skips_when_existing_file_size_matches(tmp_path):
    payload = b"x" * 50

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "HEAD":
            return httpx.Response(200, headers={"content-length": "50"})
        raise AssertionError("GET should not be called when resume hits")

    dest = tmp_path / "raw/a.fq.gz"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(payload)

    result = _download_one(
        task=_task(),
        client=_client_with(handler),
        output_root=tmp_path,
        resume=True,
        max_retries=3,
    )
    assert result.status == "skipped"
    assert result.bytes_downloaded == 50


def test_download_one_redownloads_when_existing_size_differs(tmp_path):
    payload = b"y" * 100

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "HEAD":
            return httpx.Response(200, headers={"content-length": "100"})
        return httpx.Response(200, content=payload)

    dest = tmp_path / "raw/a.fq.gz"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"short")

    result = _download_one(
        task=_task(),
        client=_client_with(handler),
        output_root=tmp_path,
        resume=True,
        max_retries=3,
    )
    assert result.status == "ok"
    assert dest.read_bytes() == payload


def test_download_one_skips_on_existence_when_head_unsupported(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "HEAD":
            raise AssertionError("HEAD should be skipped when head_supported=False")
        raise AssertionError("GET should not be called when resume hits")

    dest = tmp_path / "raw/a.fasta.gz"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"anything")

    task = _task(dest="raw/a.fasta.gz", head_supported=False)
    result = _download_one(
        task=task,
        client=_client_with(handler),
        output_root=tmp_path,
        resume=True,
        max_retries=3,
    )
    assert result.status == "skipped"


def test_download_one_retries_on_5xx_and_eventually_succeeds(tmp_path, monkeypatch):
    monkeypatch.setattr("aegis_downloader.downloader.time.sleep", lambda *_: None)
    calls = {"n": 0}
    payload = b"final"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "HEAD":
            return httpx.Response(200, headers={"content-length": str(len(payload))})
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, content=payload)

    result = _download_one(
        task=_task(),
        client=_client_with(handler),
        output_root=tmp_path,
        resume=False,
        max_retries=3,
    )
    assert result.status == "ok"
    assert calls["n"] == 3


def test_download_one_marks_failed_after_max_retries(tmp_path, monkeypatch):
    monkeypatch.setattr("aegis_downloader.downloader.time.sleep", lambda *_: None)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "HEAD":
            return httpx.Response(200, headers={"content-length": "1"})
        return httpx.Response(503)

    result = _download_one(
        task=_task(),
        client=_client_with(handler),
        output_root=tmp_path,
        resume=False,
        max_retries=2,
    )
    assert result.status == "failed"
    assert "503" in result.error


from aegis_downloader.downloader import execute_plan
from aegis_downloader.manifest import Manifest
from aegis_downloader.models import DownloadPlan, MetadataWrite


def test_execute_plan_writes_metadata_and_downloads_all_tasks(tmp_path):
    payload_a = b"AAAA"
    payload_b = b"BBBBBB"
    by_url = {
        "https://example.com/a.fq.gz": payload_a,
        "https://example.com/b.fq.gz": payload_b,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "HEAD":
            return httpx.Response(200, headers={"content-length": str(len(by_url[str(request.url)]))})
        return httpx.Response(200, content=by_url[str(request.url)])

    plan = DownloadPlan(
        tasks=[
            _task("https://example.com/a.fq.gz", "by_species/1_x/raw_data/a.fq.gz"),
            _task("https://example.com/b.fq.gz", "by_species/1_x/raw_data/b.fq.gz"),
        ],
        metadata_writes=[
            MetadataWrite(
                dest=Path("by_species/1_x/metadata.json"),
                content='{"taxId": 1}',
                description="metadata",
            )
        ],
    )
    manifest = Manifest(tmp_path / "manifest.tsv")

    result = execute_plan(
        plan=plan,
        output_root=tmp_path,
        manifest=manifest,
        client=_client_with(handler),
        workers=2,
        max_retries=0,
        resume=False,
        dry_run=False,
    )
    assert result.ok_count == 2
    assert result.failed_count == 0
    assert (tmp_path / "by_species/1_x/metadata.json").read_text() == '{"taxId": 1}'
    assert (tmp_path / "by_species/1_x/raw_data/a.fq.gz").read_bytes() == payload_a
    assert (tmp_path / "by_species/1_x/raw_data/b.fq.gz").read_bytes() == payload_b


def test_execute_plan_dry_run_writes_manifest_only(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no HTTP in dry-run")

    plan = DownloadPlan(
        tasks=[_task("https://example.com/a.fq.gz", "by_species/1_x/raw_data/a.fq.gz")],
        metadata_writes=[
            MetadataWrite(
                dest=Path("by_species/1_x/metadata.json"),
                content='{"taxId": 1}',
                description="metadata",
            )
        ],
    )
    manifest = Manifest(tmp_path / "manifest.tsv")
    result = execute_plan(
        plan=plan,
        output_root=tmp_path,
        manifest=manifest,
        client=_client_with(handler),
        workers=2,
        max_retries=0,
        resume=False,
        dry_run=True,
    )
    assert result.ok_count == 0
    # Dry-run is informational: manifest yes, everything else no.
    assert (tmp_path / "manifest.tsv").exists()
    assert not (tmp_path / "by_species/1_x/metadata.json").exists()
    assert not (tmp_path / "by_species/1_x/raw_data/a.fq.gz").exists()
