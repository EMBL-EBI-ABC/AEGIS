import argparse
import logging
import os
import sys
from pathlib import Path

import httpx

from aegis_downloader.api_client import ApiClient, PaginationCeilingError
from aegis_downloader.downloader import execute_plan
from aegis_downloader.manifest import Manifest
from aegis_downloader.planner import build_plan


_VALID_TYPES = {"raw-data", "assemblies", "annotations", "samples-metadata"}
_DEFAULT_BACKEND_URL = "https://portal.aegisearth.bio/api"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="aegis-download", description="Bulk-download AEGIS data portal content.")
    p.add_argument("--type", help="Comma-separated data types: raw-data,assemblies,annotations,samples-metadata. Default: all.")
    p.add_argument("--kingdom")
    p.add_argument("--order", dest="tax_order")
    p.add_argument("--family")
    p.add_argument("--tax-id", help="Comma-separated explicit tax IDs (intersected with other filters).")
    p.add_argument("--country")
    p.add_argument("-q", "--query", dest="q")
    p.add_argument("--output", default="./aegis-data")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument(
        "--backend-url",
        default=os.environ.get("AEGIS_BACKEND_URL", _DEFAULT_BACKEND_URL),
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--manifest")
    p.add_argument("--manifest-format", choices=["tsv", "json"], default="tsv")
    p.add_argument("--no-resume", action="store_true")
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])
    return p


def parse_types(raw: str | None) -> set[str]:
    if not raw:
        return set(_VALID_TYPES)
    values = {v.strip() for v in raw.split(",") if v.strip()}
    unknown = values - _VALID_TYPES
    if unknown:
        raise SystemExit(f"unknown --type value(s): {', '.join(sorted(unknown))}; valid: {', '.join(sorted(_VALID_TYPES))}")
    return values


def _make_transport() -> httpx.BaseTransport | None:
    """Returns None to use httpx's default transport. Tests monkeypatch this."""
    return None


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=args.log_level.upper(), format="%(levelname)s %(message)s")

    workers = max(1, min(32, args.workers))
    output_root = Path(args.output)
    manifest_path = Path(args.manifest) if args.manifest else output_root / ("manifest.json" if args.manifest_format == "json" else "manifest.tsv")

    types = parse_types(args.type)
    explicit_tax_ids: set[int] | None = None
    if args.tax_id:
        try:
            explicit_tax_ids = {int(v.strip()) for v in args.tax_id.split(",") if v.strip()}
        except ValueError:
            print("--tax-id must be a comma-separated list of integers", file=sys.stderr)
            return 2

    server_filters: dict[str, str | int | None] = {
        "kingdom": args.kingdom,
        "tax_order": args.tax_order,
        "family": args.family,
        "countries": args.country,
        "q": args.q,
    }

    transport = _make_transport()
    http_client = httpx.Client(timeout=30.0, transport=transport)
    api_client = ApiClient(args.backend_url, transport=transport)

    try:
        try:
            plan = build_plan(
                client=api_client,
                types=types,
                server_filters=server_filters,
                explicit_tax_ids=explicit_tax_ids,
            )
        except PaginationCeilingError as exc:
            print(str(exc), file=sys.stderr)
            return 3
        except httpx.HTTPError as exc:
            print(f"BE unreachable: {exc}", file=sys.stderr)
            return 3

        manifest = Manifest(manifest_path, format=args.manifest_format)
        result = execute_plan(
            plan=plan,
            output_root=output_root,
            manifest=manifest,
            client=http_client,
            workers=workers,
            max_retries=args.max_retries,
            resume=not args.no_resume,
            dry_run=args.dry_run,
        )

        print(f"Done. ok={result.ok_count} skipped={result.skipped_count} failed={result.failed_count}")
        return 1 if result.failed_count > 0 else 0
    finally:
        http_client.close()
        api_client.close()


def main() -> int:
    return run()
