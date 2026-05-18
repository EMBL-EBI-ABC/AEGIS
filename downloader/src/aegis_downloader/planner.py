import json
from collections.abc import Iterable

from aegis_downloader.api_client import ApiClient
from aegis_downloader.extractors import (
    extract_annotations,
    extract_assemblies,
    extract_raw_data,
    slugify,
)
from aegis_downloader.models import DownloadPlan, MetadataWrite
from pathlib import Path


_EXTRACTORS = {
    "raw-data": extract_raw_data,
    "assemblies": extract_assemblies,
    "annotations": extract_annotations,
}


def build_plan(
    *,
    client: ApiClient,
    types: Iterable[str],
    server_filters: dict[str, str | int | None],
    explicit_tax_ids: set[int] | None,
) -> DownloadPlan:
    types = set(types)
    selected_extractors = [_EXTRACTORS[t] for t in types if t in _EXTRACTORS]
    plan = DownloadPlan()

    records_for_samples: list[dict] = []
    for record in client.iter_data_portal(filters=server_filters):
        if explicit_tax_ids is not None and record["taxId"] not in explicit_tax_ids:
            continue
        slug = slugify(record["scientificName"])
        plan.metadata_writes.append(
            MetadataWrite(
                dest=Path(f"by_species/{record['taxId']}_{slug}/metadata.json"),
                content=json.dumps(record, indent=2),
                description=f"metadata.json for tax_id {record['taxId']}",
            )
        )
        records_for_samples.append(record)
        for extractor in selected_extractors:
            plan.tasks.extend(extractor(record))

    if "samples-metadata" in types:
        plan.metadata_writes.append(_collect_samples_metadata(client, records_for_samples))

    return plan


def _collect_samples_metadata(client: ApiClient, records: list[dict]) -> MetadataWrite:
    all_samples: list[dict] = []
    for record in records:
        all_samples.extend(client.iter_samples(filters={"taxId": record["taxId"]}, page_size=1000))
    return MetadataWrite(
        dest=Path("samples_metadata.tsv"),
        content=_samples_to_tsv(all_samples),
        description=f"samples_metadata.tsv ({len(all_samples)} rows)",
    )


def _samples_to_tsv(samples: list[dict]) -> str:
    if not samples:
        return "accession\ttaxId\tscientificName\n"
    columns = sorted({k for s in samples for k in s.keys()})
    lines = ["\t".join(columns)]
    for s in samples:
        lines.append("\t".join(_tsv_value(s.get(c)) for c in columns))
    return "\n".join(lines) + "\n"


def _tsv_value(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, separators=(",", ":"))
    return str(v).replace("\t", " ").replace("\n", " ")
