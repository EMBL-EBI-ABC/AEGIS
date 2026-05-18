from pathlib import Path

from aegis_downloader.manifest import Manifest
from aegis_downloader.models import DownloadTask, FileResult


def _task(url: str, dest: str, data_type: str = "raw-data") -> DownloadTask:
    return DownloadTask(
        url=url,
        dest=Path(dest),
        data_type=data_type,
        tax_id=43171,
        scientific_name="Linaria vulgaris",
    )


def test_write_initial_creates_tsv_with_header_and_pending_rows(tmp_path):
    manifest_path = tmp_path / "manifest.tsv"
    manifest = Manifest(manifest_path, format="tsv")
    tasks = [
        _task("https://example.com/a.fq.gz", "by_species/43171_x/raw_data/a.fq.gz"),
        _task("https://example.com/b.fq.gz", "by_species/43171_x/raw_data/b.fq.gz"),
    ]
    manifest.write_initial(tasks)

    content = manifest_path.read_text()
    header, *rows = content.strip().split("\n")
    assert header.split("\t") == [
        "tax_id", "scientific_name", "data_type", "url", "dest",
        "expected_size", "bytes_downloaded", "status", "error",
    ]
    assert len(rows) == 2
    assert rows[0].endswith("\tpending\t")


def test_update_replaces_row_for_completed_task(tmp_path):
    manifest_path = tmp_path / "manifest.tsv"
    manifest = Manifest(manifest_path, format="tsv")
    task = _task("https://example.com/a.fq.gz", "by_species/43171_x/raw_data/a.fq.gz")
    manifest.write_initial([task])

    result = FileResult(task=task, status="ok", bytes_downloaded=1024, expected_size=1024)
    manifest.update(result)

    rows = manifest_path.read_text().strip().split("\n")[1:]
    fields = rows[0].split("\t")
    assert fields[5] == "1024"      # expected_size
    assert fields[6] == "1024"      # bytes_downloaded
    assert fields[7] == "ok"        # status
