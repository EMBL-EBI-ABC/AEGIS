import time
from pathlib import Path

import httpx

from aegis_downloader.models import DownloadTask, FileResult


_CHUNK_SIZE = 1024 * 1024


def _download_one(
    *,
    task: DownloadTask,
    client: httpx.Client,
    output_root: Path,
    resume: bool,
    max_retries: int,
) -> FileResult:
    dest = output_root / task.dest

    expected_size: int | None = None
    if task.head_supported:
        try:
            head = client.head(task.url, follow_redirects=True)
            if head.is_success and "content-length" in head.headers:
                expected_size = int(head.headers["content-length"])
        except httpx.HTTPError:
            pass

    if resume and dest.exists():
        on_disk = dest.stat().st_size
        if expected_size is None or on_disk == expected_size:
            return FileResult(task=task, status="skipped", bytes_downloaded=on_disk, expected_size=expected_size)

    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".partial")

    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            bytes_written = 0
            with client.stream("GET", task.url, follow_redirects=True) as response:
                response.raise_for_status()
                with open(partial, "wb") as f:
                    for chunk in response.iter_bytes(_CHUNK_SIZE):
                        f.write(chunk)
                        bytes_written += len(chunk)
            partial.rename(dest)
            return FileResult(task=task, status="ok", bytes_downloaded=bytes_written, expected_size=expected_size)
        except (httpx.HTTPStatusError, httpx.TransportError) as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    return FileResult(task=task, status="failed", bytes_downloaded=0, expected_size=expected_size, error=str(last_err))
