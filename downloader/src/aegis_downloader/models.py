from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

DataType = Literal["raw-data", "assemblies", "annotations", "samples-metadata"]
Status = Literal["pending", "skipped", "ok", "failed"]


@dataclass
class DownloadTask:
    url: str
    dest: Path                       # relative to output_root
    data_type: DataType
    tax_id: int
    scientific_name: str
    expected_size: int | None = None
    head_supported: bool = True


@dataclass
class MetadataWrite:
    """A non-network write — JSON or TSV blob to put on disk before downloads start."""
    dest: Path                       # relative to output_root
    content: str
    description: str                 # for logging, e.g. "metadata.json for tax_id 43171"


@dataclass
class DownloadPlan:
    tasks: list[DownloadTask] = field(default_factory=list)
    metadata_writes: list[MetadataWrite] = field(default_factory=list)

    @property
    def total_tasks(self) -> int:
        return len(self.tasks)


@dataclass
class FileResult:
    task: DownloadTask
    status: Status
    bytes_downloaded: int = 0
    expected_size: int | None = None
    error: str = ""
