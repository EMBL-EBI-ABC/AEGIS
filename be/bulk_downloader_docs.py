# be/bulk_downloader_docs.py
"""The aegis-download README, inlined as a string so it ships in the BE container."""

README_TEXT = """# aegis-downloader

Bulk-download AEGIS data portal content (raw reads, assemblies, annotations, samples metadata), filtered by data type and phylogeny.

## Install

```bash
cd downloader
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Quick start

Download all data types for one species:

```bash
aegis-download --tax-id 43171 --output ./aegis-data
```

Download annotations only for all *Lepidoptera*:

```bash
aegis-download --type annotations --order Lepidoptera --output ./lepidoptera
```

Preview what would be downloaded without fetching anything:

```bash
aegis-download --type raw-data --kingdom Animalia --dry-run
```

## Flags

| Flag | Default | Notes |
|---|---|---|
| `--type` | all four | `raw-data`, `assemblies`, `annotations`, `samples-metadata` (comma-separated) |
| `--kingdom` / `--order` / `--family` | — | Phylogeny filters |
| `--tax-id` | — | Comma-separated explicit tax IDs |
| `--country` | — | Country filter (passthrough to BE `countries`) |
| `-q` / `--query` | — | Full-text search |
| `--output` | `./aegis-data` | Output root directory |
| `--workers` | 8 | Concurrent downloads (capped at 32) |
| `--backend-url` | `https://portal.aegisearth.bio/api` | Or set `AEGIS_BACKEND_URL` |
| `--dry-run` | false | Build manifest without downloading |
| `--manifest` | `manifest.tsv` under `--output` | Manifest output path |
| `--manifest-format` | `tsv` | Or `json` |
| `--no-resume` | resume on | Skip the resume check, redownload everything |
| `--max-retries` | 3 | Per-file retries with exponential backoff |
| `--log-level` | `info` | `debug` / `info` / `warning` / `error` |

## Data types

- **`raw-data`** — gzipped FASTQ run files from ENA (paired-end split by `;` in `fastq_ftp`).
- **`assemblies`** — gzipped FASTA of every sequence per assembly, fetched from ENA's browser API (`https://www.ebi.ac.uk/ena/browser/api/fasta/<acc>.<ver>?download=true&gzip=true`). One file per assembly entry on the species record.
- **`annotations`** — Ensembl annotation files (GTF, GFF3, and protein / transcript / softmasked-genome / repeat-library FASTA) grouped by assembly accession.
- **`samples-metadata`** — TSV dump of BioSamples records associated with the selected species.

## Output layout

```
<output>/
  manifest.tsv
  samples_metadata.tsv          # if samples-metadata is requested
  by_species/
    43171_linaria_vulgaris/
      metadata.json
      raw_data/
        ERR10828371_1.fastq.gz
        ERR10828371_2.fastq.gz
      assemblies/
        GCA_948329855.1.fasta.gz
        GCA_948329865.1.fasta.gz
      annotations/
        GCA_948329865.1/
          <annotation files>
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success (or dry-run completed) |
| 1 | One or more files failed after retries |
| 2 | Invalid arguments |
| 3 | BE unreachable / planning aborted |

## Pagination ceiling

The AEGIS BE caps result-set pagination at 10 000 records (Elasticsearch `index.max_result_window`). If your filter matches more, the tool exits with a clear error — narrow the filter (e.g. add `--order` or `--family`) and retry.

## Development

```bash
pip install -e ".[dev]"
pytest -v
```
"""
