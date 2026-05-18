import re
from pathlib import Path

from aegis_downloader.models import DownloadTask


_SLUG_RE = re.compile(r"[^a-zA-Z0-9]+")


def slugify(name: str) -> str:
    return _SLUG_RE.sub("_", name).strip("_").lower()


def extract_raw_data(record: dict) -> list[DownloadTask]:
    tax_id = record["taxId"]
    scientific_name = record["scientificName"]
    slug = slugify(scientific_name)
    tasks: list[DownloadTask] = []
    for entry in record.get("rawData") or []:
        for path in (entry.get("fastq_ftp") or "").split(";"):
            path = path.strip()
            if not path:
                continue
            filename = path.rsplit("/", 1)[-1]
            tasks.append(
                DownloadTask(
                    url=f"https://{path}",
                    dest=Path(f"by_species/{tax_id}_{slug}/raw_data/{filename}"),
                    data_type="raw-data",
                    tax_id=tax_id,
                    scientific_name=scientific_name,
                    head_supported=True,
                )
            )
    return tasks
