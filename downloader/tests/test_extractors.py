import json
from pathlib import Path

from aegis_downloader.extractors import slugify, extract_raw_data


FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_slugify_lowercases_and_replaces_spaces():
    assert slugify("Linaria vulgaris") == "linaria_vulgaris"


def test_slugify_collapses_runs_of_non_alphanumerics():
    assert slugify("Homo sapiens (modern)") == "homo_sapiens_modern"


def test_slugify_strips_leading_and_trailing_underscores():
    assert slugify("  Drosophila melanogaster  ") == "drosophila_melanogaster"


def test_slugify_keeps_digits():
    assert slugify("E. coli K12") == "e_coli_k12"


def test_extract_raw_data_splits_semicolon_separated_fastq_ftp():
    record = _load("data_portal_43171.json")
    tasks = extract_raw_data(record)
    assert len(tasks) == 2
    urls = [t.url for t in tasks]
    assert urls == [
        "https://ftp.sra.ebi.ac.uk/vol1/fastq/ERR108/001/ERR10828371/ERR10828371_1.fastq.gz",
        "https://ftp.sra.ebi.ac.uk/vol1/fastq/ERR108/001/ERR10828371/ERR10828371_2.fastq.gz",
    ]
    assert tasks[0].dest == Path("by_species/43171_linaria_vulgaris/raw_data/ERR10828371_1.fastq.gz")
    assert tasks[0].data_type == "raw-data"
    assert tasks[0].tax_id == 43171
    assert tasks[0].scientific_name == "Linaria vulgaris"
    assert tasks[0].head_supported is True


def test_extract_raw_data_handles_missing_rawdata_field():
    tasks = extract_raw_data({"taxId": 1, "scientificName": "X", "rawData": None})
    assert tasks == []


def test_extract_raw_data_skips_empty_url_fragments():
    record = {
        "taxId": 1,
        "scientificName": "X",
        "rawData": [{"fastq_ftp": "a/b/c.fastq.gz;;d/e/f.fastq.gz"}],
    }
    tasks = extract_raw_data(record)
    assert [t.url for t in tasks] == ["https://a/b/c.fastq.gz", "https://d/e/f.fastq.gz"]
