import re
from pathlib import Path

from aegis_downloader.models import DownloadTask

ENSEMBL_RAPID_RELEASE_BASE = "https://ftp.ebi.ac.uk/pub/ensemblorganisms"


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
        assembly_name = safe_component(annotation.get("assemblyName") or "unknown")
        for file_key in ("annotationFiles", "assemblyFiles", "homologyFiles"):
            for entry in annotation.get(file_key) or []:
                path = entry.get("path")
                if not path:
                    continue
                filename = safe_component(entry.get("name") or path.rsplit("/", 1)[-1])
                tasks.append(
                    DownloadTask(
                        url=f"{ENSEMBL_RAPID_RELEASE_BASE}/{path}",
                        dest=Path(f"by_species/{tax_id}_{slug}/annotations/{assembly_name}/{filename}"),
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
