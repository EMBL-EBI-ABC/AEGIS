import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import httpx
from rich.progress import BarColumn, DownloadColumn, Progress, TaskID, TextColumn, TimeRemainingColumn

from aegis_downloader.manifest import Manifest
from aegis_downloader.models import DownloadPlan, DownloadTask, FileResult


_CHUNK_SIZE = 1024 * 1024


def _resolve_within(output_root: Path, dest: Path) -> Path:
    """Resolve ``dest`` under ``output_root`` and refuse anything that escapes it.

    ``dest`` is built from server-supplied strings (assembly names, file names,
    FTP basenames). ``pathlib`` does not collapse ``..`` on join, so without this
    check a record containing traversal segments could write outside the output
    directory (CWE-22). Fail closed instead.
    """
    base = output_root.resolve()
    full = (base / dest).resolve()
    if base != full and not full.is_relative_to(base):
        raise ValueError(f"refusing to write outside output dir: {dest}")
    return full


def _download_one(
    *,
    task: DownloadTask,
    client: httpx.Client,
    output_root: Path,
    resume: bool,
    max_retries: int,
    on_total: Callable[[int | None], None] | None = None,
    on_chunk: Callable[[int], None] | None = None,
) -> FileResult:
    try:
        dest = _resolve_within(output_root, task.dest)
    except ValueError as e:
        return FileResult(task=task, status="failed", bytes_downloaded=0, error=str(e))

    expected_size: int | None = None
    if task.head_supported:
        try:
            head = client.head(task.url, follow_redirects=True)
            if head.is_success and "content-length" in head.headers:
                expected_size = int(head.headers["content-length"])
        except httpx.HTTPError:
            pass

    if on_total is not None:
        on_total(expected_size)

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
                        n = len(chunk)
                        bytes_written += n
                        if on_chunk is not None:
                            on_chunk(n)
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
        dest = _resolve_within(output_root, write.dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(write.content)

    ok = skipped = failed = 0
    with ThreadPoolExecutor(max_workers=workers) as pool, Progress(
        TextColumn("[cyan]{task.description}[/]"),
        BarColumn(),
        DownloadColumn(),
        TimeRemainingColumn(),
    ) as bar:
        bar_tasks: dict[str, TaskID] = {
            str(task.dest): bar.add_task(task.dest.name, total=None, start=False)
            for task in plan.tasks
        }

        def _callbacks_for(task: DownloadTask) -> tuple[Callable[[int | None], None], Callable[[int], None]]:
            tid = bar_tasks[str(task.dest)]

            def set_total(size: int | None) -> None:
                # Start the task only when we have something to advance — otherwise
                # ENA's no-Content-Length downloads would never show elapsed time.
                bar.start_task(tid)
                if size is not None:
                    bar.update(tid, total=size)

            def advance(n: int) -> None:
                bar.advance(tid, n)

            return set_total, advance

        futures = {}
        for task in plan.tasks:
            set_total, advance = _callbacks_for(task)
            futures[pool.submit(
                _download_one,
                task=task,
                client=client,
                output_root=output_root,
                resume=resume,
                max_retries=max_retries,
                on_total=set_total,
                on_chunk=advance,
            )] = task

        for future in as_completed(futures):
            result = future.result()
            manifest.update(result)
            tid = bar_tasks[str(result.task.dest)]
            if result.status == "skipped":
                bar.start_task(tid)
                size = result.bytes_downloaded or 1
                bar.update(tid, total=size, completed=size,
                           description=f"[dim]{result.task.dest.name} (skipped)[/]")
                skipped += 1
            elif result.status == "failed":
                bar.update(tid, description=f"[red]{result.task.dest.name} (failed)[/]")
                failed += 1
            else:
                ok += 1

    return ExecutionResult(ok_count=ok, skipped_count=skipped, failed_count=failed)
