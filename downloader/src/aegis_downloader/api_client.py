from collections.abc import Iterator

import httpx


MAX_RESULT_WINDOW = 10000


class PaginationCeilingError(RuntimeError):
    pass


class ApiClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self._base = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def close(self) -> None:
        self._client.close()

    def iter_data_portal(
        self,
        filters: dict[str, str | int | None],
        *,
        page_size: int = 100,
    ) -> Iterator[dict]:
        return self._paginate("/data_portal", filters, page_size)

    def get_data_portal_record(self, tax_id: int) -> dict | None:
        response = self._client.get(f"{self._base}/data_portal/{tax_id}")
        response.raise_for_status()
        results = response.json().get("results", [])
        return results[0] if results else None

    def iter_samples(
        self,
        filters: dict[str, str | int | None],
        *,
        page_size: int = 1000,
    ) -> Iterator[dict]:
        return self._paginate("/samples", filters, page_size)

    def _paginate(
        self,
        path: str,
        filters: dict[str, str | int | None],
        page_size: int,
    ) -> Iterator[dict]:
        cleaned = {k: v for k, v in filters.items() if v is not None}
        start = 0
        while True:
            params = {**cleaned, "start": start, "size": page_size}
            response = self._client.get(f"{self._base}{path}", params=params)
            response.raise_for_status()
            body = response.json()
            total = body.get("total", 0)
            if total > MAX_RESULT_WINDOW:
                raise PaginationCeilingError(
                    f"Filter matches {total} records; AEGIS BE caps pagination at "
                    f"{MAX_RESULT_WINDOW} — narrow your filter."
                )
            results = body.get("results", [])
            yield from results
            start += len(results)
            if start >= total or not results:
                return
