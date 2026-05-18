from aegis_downloader.extractors import slugify


def test_slugify_lowercases_and_replaces_spaces():
    assert slugify("Linaria vulgaris") == "linaria_vulgaris"


def test_slugify_collapses_runs_of_non_alphanumerics():
    assert slugify("Homo sapiens (modern)") == "homo_sapiens_modern"


def test_slugify_strips_leading_and_trailing_underscores():
    assert slugify("  Drosophila melanogaster  ") == "drosophila_melanogaster"


def test_slugify_keeps_digits():
    assert slugify("E. coli K12") == "e_coli_k12"
