import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import httpx
from rich.progress import BarColumn, DownloadColumn, Progress, TaskProgressColumn, TextColumn, TimeRemainingColumn

from aegis_downloader.manifest import Manifest
from aegis_downloader.models import DownloadPlan, DownloadTask, FileResult


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


@dataclass
class ExecutionResult:
    ok_count: int
    skipped_count: int
    failed_count: int


def execute_plan(
    *,
    plan: DownloadPlan,
    output_root: Path,
    manifest: Manifest,
    client: httpx.Client,
    workers: int,
    max_retries: int,
    resume: bool,
    dry_run: bool,
) -> ExecutionResult:
    output_root.mkdir(parents=True, exist_ok=True)
    manifest.write_initial(plan.tasks)

    if dry_run:
        # Dry-run = manifest only; no filesystem side effects beyond that.
        return ExecutionResult(ok_count=0, skipped_count=0, failed_count=0)

    for write in plan.metadata_writes:
        dest = output_root / write.dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(write.content)

    ok = skipped = failed = 0
    with ThreadPoolExecutor(max_workers=workers) as pool, Progress(
        TextColumn("[bold]Downloading[/bold]"),
        BarColumn(),
        TaskProgressColumn(),
        DownloadColumn(),
        TimeRemainingColumn(),
    ) as bar:
        bar_task = bar.add_task("files", total=len(plan.tasks))
        futures = {
            pool.submit(
                _download_one,
                task=task,
                client=client,
                output_root=output_root,
                resume=resume,
                max_retries=max_retries,
            ): task
            for task in plan.tasks
        }
        for future in as_completed(futures):
            result = future.result()
            manifest.update(result)
            bar.advance(bar_task)
            if result.status == "ok":
                ok += 1
            elif result.status == "skipped":
                skipped += 1
            else:
                failed += 1

    return ExecutionResult(ok_count=ok, skipped_count=skipped, failed_count=failed)
