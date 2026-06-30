import re
from pathlib import Path

from aegis_downloader.models import DownloadTask

_SLUG_RE = re.compile(r"[^a-zA-Z0-9]+")


def slugify(name: str) -> str:
    return _SLUG_RE.sub("_", name).strip("_").lower()


def safe_component(value: str, fallback: str = "unknown") -> str:
    """Reduce a server-supplied string to a single safe path component.

    Server-controlled fields (assembly names, annotation file names, FTP
    basenames) are interpolated into download destinations. ``Path(value).name``
    drops any directory parts, so embedded ``/`` or ``..`` traversal sequences
    cannot widen the path. Empty/dot-only results fall back to a constant.
    """
    name = Path(str(value)).name
    if name in ("", ".", ".."):
        return fallback
    return name


def extract_annotations(record: dict) -> list[DownloadTask]:
    tax_id = record["taxId"]
    scientific_name = record["scientificName"]
    slug = slugify(scientific_name)
    tasks: list[DownloadTask] = []
    for annotation in record.get("annotations") or []:
        accession = safe_component(annotation.get("accession") or "unknown")
        # Each annotation record carries absolute file URLs grouped by kind.
        # other_data.ftp_dumps / view_in_browser are browse links, not files, so
        # they are intentionally skipped here. repeat_library may be null.
        ann = annotation.get("annotation") or {}
        file_urls = [
            ann.get("GTF"),
            ann.get("GFF3"),
            (annotation.get("proteins") or {}).get("FASTA"),
            (annotation.get("transcripts") or {}).get("FASTA"),
            (annotation.get("softmasked_genome") or {}).get("FASTA"),
            (annotation.get("repeat_library") or {}).get("FASTA"),
        ]
        for url in file_urls:
            if not url:
                continue
            filename = safe_component(url.rsplit("/", 1)[-1])
            tasks.append(
                DownloadTask(
                    url=url,
                    dest=Path(f"by_species/{tax_id}_{slug}/annotations/{accession}/{filename}"),
                    data_type="annotations",
                    tax_id=tax_id,
                    scientific_name=scientific_name,
                    head_supported=True,
                )
            )
    return tasks


ENA_BROWSER_FASTA_BASE = "https://www.ebi.ac.uk/ena/browser/api/fasta"


def extract_assemblies(record: dict) -> list[DownloadTask]:
    tax_id = record["taxId"]
    scientific_name = record["scientificName"]
    slug = slugify(scientific_name)
    tasks: list[DownloadTask] = []
    for entry in record.get("assemblies") or []:
        accession = entry.get("accession")
        if not accession:
            continue
        version = entry.get("version")
        ref = f"{accession}.{version}" if version else accession
        url = f"{ENA_BROWSER_FASTA_BASE}/{ref}?download=true&gzip=true"
        filename = safe_component(f"{ref}.fasta.gz")
        tasks.append(
            DownloadTask(
                url=url,
                dest=Path(f"by_species/{tax_id}_{slug}/assemblies/{filename}"),
                data_type="assemblies",
                tax_id=tax_id,
                scientific_name=scientific_name,
                head_supported=False,
            )
        )
    return tasks


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
            filename = safe_component(path.rsplit("/", 1)[-1])
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
