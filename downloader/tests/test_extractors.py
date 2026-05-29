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


from aegis_downloader.extractors import extract_annotations


def test_extract_annotations_pulls_all_three_file_types():
    record = _load("data_portal_43171.json")
    tasks = extract_annotations(record)
    assert len(tasks) == 3
    urls = sorted(t.url for t in tasks)
    assert urls == [
        "https://ftp.ebi.ac.uk/pub/ensemblorganisms/linaria_vulgaris/GCA_948329865.1/ensembl/geneset/2024_03/genes.gff3.gz",
        "https://ftp.ebi.ac.uk/pub/ensemblorganisms/linaria_vulgaris/GCA_948329865.1/ensembl/genome/softmasked.fa.gz",
        "https://ftp.ebi.ac.uk/pub/ensemblorganisms/linaria_vulgaris/GCA_948329865.1/ensembl/homology/2024_03/homology.tsv.gz",
    ]
    for task in tasks:
        assert task.data_type == "annotations"
        assert task.head_supported is True
        assert task.dest.parts[:3] == ("by_species", "43171_linaria_vulgaris", "annotations")
        assert task.dest.parts[3] == "daLinVulg1.1"


def test_extract_annotations_neutralizes_traversal_in_assembly_name_and_filename():
    record = {
        "taxId": 1,
        "scientificName": "X",
        "annotations": [
            {
                "assemblyName": "../../../../etc",
                "annotationFiles": [
                    {"path": "ok/genes.gff3.gz", "name": "../../../../../../tmp/evil.sh"},
                ],
            }
        ],
    }
    tasks = extract_annotations(record)
    assert len(tasks) == 1
    # No path component may be a traversal sequence; the dest stays under the species dir.
    assert ".." not in tasks[0].dest.parts
    assert tasks[0].dest.parts[:3] == ("by_species", "1_x", "annotations")
    assert tasks[0].dest.parts[3] == "etc"
    assert tasks[0].dest.name == "evil.sh"
    # The download URL still uses the original server path.
    assert tasks[0].url.endswith("/ok/genes.gff3.gz")


def test_extract_annotations_handles_missing_annotations_field():
    assert extract_annotations({"taxId": 1, "scientificName": "X", "annotations": None}) == []


def test_extract_annotations_skips_empty_file_lists():
    record = {
        "taxId": 1,
        "scientificName": "X",
        "annotations": [{"assemblyName": "a1", "annotationFiles": [], "assemblyFiles": None, "homologyFiles": []}],
    }
    assert extract_annotations(record) == []


from aegis_downloader.extractors import extract_assemblies


def test_extract_assemblies_builds_ena_url_with_version():
    record = _load("data_portal_43171.json")
    tasks = extract_assemblies(record)
    assert len(tasks) == 2
    urls = sorted(t.url for t in tasks)
    assert urls == [
        "https://www.ebi.ac.uk/ena/browser/api/fasta/GCA_948329855.1?download=true&gzip=true",
        "https://www.ebi.ac.uk/ena/browser/api/fasta/GCA_948329865.1?download=true&gzip=true",
    ]
    dests = sorted(str(t.dest) for t in tasks)
    assert dests == [
        "by_species/43171_linaria_vulgaris/assemblies/GCA_948329855.1.fasta.gz",
        "by_species/43171_linaria_vulgaris/assemblies/GCA_948329865.1.fasta.gz",
    ]
    for task in tasks:
        assert task.data_type == "assemblies"
        assert task.head_supported is False


def test_extract_assemblies_omits_version_when_missing():
    record = {
        "taxId": 1, "scientificName": "X",
        "assemblies": [{"accession": "GCA_999", "version": None, "assembly_name": "x"}],
    }
    tasks = extract_assemblies(record)
    assert tasks[0].url == "https://www.ebi.ac.uk/ena/browser/api/fasta/GCA_999?download=true&gzip=true"
    assert tasks[0].dest.name == "GCA_999.fasta.gz"


def test_extract_assemblies_handles_missing_assemblies_field():
    assert extract_assemblies({"taxId": 1, "scientificName": "X", "assemblies": None}) == []
