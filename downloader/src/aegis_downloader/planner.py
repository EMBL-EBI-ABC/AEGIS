from collections.abc import Iterable

from aegis_downloader.api_client import ApiClient
from aegis_downloader.extractors import (
    extract_annotations,
    extract_assemblies,
    extract_raw_data,
)
from aegis_downloader.models import DownloadPlan, DownloadTask


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
    for record in client.iter_data_portal(filters=server_filters):
        if explicit_tax_ids is not None and record["taxId"] not in explicit_tax_ids:
            continue
        for extractor in selected_extractors:
            plan.tasks.extend(extractor(record))
    return plan
