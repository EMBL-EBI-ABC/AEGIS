import json
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

from aegis_downloader.models import DownloadTask, FileResult


_COLUMNS = [
    "tax_id", "scientific_name", "data_type", "url", "dest",
    "expected_size", "bytes_downloaded", "status", "error",
]


@dataclass
class _Row:
    tax_id: int
    scientific_name: str
    data_type: str
    url: str
    dest: str
    expected_size: str = ""
    bytes_downloaded: str = "0"
    status: str = "pending"
    error: str = ""


@dataclass
class Manifest:
    path: Path
    format: str = "tsv"          # "tsv" or "json"
    _rows: list[_Row] = field(default_factory=list)
    _index: dict[str, int] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def write_initial(self, tasks: list[DownloadTask]) -> None:
        self._rows = []
        self._index = {}
        for task in tasks:
            key = str(task.dest)
            self._index[key] = len(self._rows)
            self._rows.append(_Row(
                tax_id=task.tax_id,
                scientific_name=task.scientific_name,
                data_type=task.data_type,
                url=task.url,
                dest=key,
                expected_size=str(task.expected_size) if task.expected_size is not None else "",
            ))
        self._flush()

    def update(self, result: FileResult) -> None:
        with self._lock:
            idx = self._index[str(result.task.dest)]
            row = self._rows[idx]
            row.status = result.status
            row.bytes_downloaded = str(result.bytes_downloaded)
            if result.expected_size is not None:
                row.expected_size = str(result.expected_size)
            row.error = result.error
            self._flush()

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.format == "json":
            payload = [self._row_to_dict(r) for r in self._rows]
            self.path.write_text(json.dumps(payload, indent=2))
        else:
            lines = ["\t".join(_COLUMNS)]
            for r in self._rows:
                lines.append("\t".join(_tsv_escape(getattr(r, c)) for c in _COLUMNS))
            self.path.write_text("\n".join(lines) + "\n")

    @staticmethod
    def _row_to_dict(row: _Row) -> dict:
        return {c: getattr(row, c) for c in _COLUMNS}


def _tsv_escape(v) -> str:
    return str(v).replace("\t", " ").replace("\n", " ")
