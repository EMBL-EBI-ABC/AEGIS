import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(
    __name__,
    path="/bulk-download",
    title="Bulk Download - AEGIS",
)


REPO_URL = "https://github.com/EMBL-EBI-ABC/AEGIS"
PACKAGE_URL = f"{REPO_URL}/tree/main/downloader"
README_URL = f"{REPO_URL}/blob/main/downloader/README.md"


def _section_heading(text: str) -> html.H2:
    return html.H2(
        text,
        style={
            "fontFamily": "var(--font-display)",
            "fontSize": "1.5rem",
            "color": "var(--aegis-text-primary)",
            "marginTop": "2.5rem",
            "marginBottom": "0.75rem",
        },
    )


def _code_block(text: str) -> html.Pre:
    return html.Pre(
        html.Code(text),
        style={
            "background": "var(--aegis-bg-elevated)",
            "color": "var(--aegis-text-primary)",
            "border": "1px solid var(--aegis-border-subtle)",
            "borderRadius": "var(--radius-md)",
            "padding": "1rem 1.25rem",
            "fontFamily": "var(--font-mono)",
            "fontSize": "0.85rem",
            "lineHeight": "1.5",
            "overflowX": "auto",
            "marginBottom": "1rem",
        },
    )


def _inline_code(text: str) -> html.Code:
    return html.Code(
        text,
        style={
            "fontFamily": "var(--font-mono)",
            "fontSize": "0.85em",
            "color": "var(--aegis-accent-primary)",
            "background": "var(--aegis-bg-elevated)",
            "padding": "0.1rem 0.35rem",
            "borderRadius": "3px",
        },
    )


def _info_card(label: str, value, icon: str | None = None, link: str | None = None) -> html.Div:
    value_el = html.Code(
        value,
        style={
            "color": "var(--aegis-accent-primary)",
            "fontFamily": "var(--font-mono)",
            "fontSize": "0.85rem",
        },
    )
    if link:
        value_el = html.A(
            value_el,
            href=link,
            target="_blank",
            rel="noopener noreferrer",
            style={"textDecoration": "underline", "textUnderlineOffset": "3px"},
        )

    contents = []
    if icon:
        contents.append(
            html.Img(
                src=icon,
                style={
                    "width": "1.75rem",
                    "height": "1.75rem",
                    "marginBottom": "0.5rem",
                    "opacity": "0.85",
                },
            )
        )
    contents.extend(
        [
            html.Div(
                label,
                style={
                    "fontSize": "0.75rem",
                    "color": "var(--aegis-text-muted)",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.05em",
                },
            ),
            value_el,
        ]
    )

    return html.Div(
        contents,
        style={
            "padding": "1rem",
            "background": "var(--aegis-bg-card)",
            "borderRadius": "var(--radius-md)",
            "border": "1px solid var(--aegis-border-subtle)",
            "textAlign": "center",
        },
    )


def _flag_row(flag: str, default: str, notes) -> html.Tr:
    return html.Tr(
        [
            html.Td(_inline_code(flag), style={"verticalAlign": "top", "padding": "0.55rem 0.75rem"}),
            html.Td(default, style={"verticalAlign": "top", "padding": "0.55rem 0.75rem", "color": "var(--aegis-text-muted)"}),
            html.Td(notes, style={"verticalAlign": "top", "padding": "0.55rem 0.75rem", "color": "var(--aegis-text-secondary)"}),
        ]
    )


_FLAG_ROWS = [
    ("--type", "all four", ["Comma-separated. Values: ", _inline_code("raw-data"), ", ", _inline_code("assemblies"), ", ", _inline_code("annotations"), ", ", _inline_code("samples-metadata"), "."]),
    ("--kingdom / --order / --family", "—", "Phylogeny filters (server-side)."),
    ("--tax-id", "—", "Comma-separated explicit tax IDs (intersected with other filters)."),
    ("--country", "—", "Country filter (passthrough to BE)."),
    ("-q / --query", "—", "Full-text search."),
    ("--output", "./aegis-data", "Output root directory."),
    ("--workers", "8", "Concurrent downloads (capped at 32)."),
    ("--backend-url", "portal.aegisearth.bio/api", ["Or set ", _inline_code("AEGIS_BACKEND_URL"), " env var."]),
    ("--dry-run", "false", "Build the manifest without downloading."),
    ("--manifest", "manifest.tsv", "Manifest output path."),
    ("--manifest-format", "tsv", ["Or ", _inline_code("json"), "."]),
    ("--no-resume", "resume on", "Redownload everything; skip the resume check."),
    ("--max-retries", "3", "Per-file retries with exponential backoff."),
    ("--log-level", "info", ["One of ", _inline_code("debug"), ", ", _inline_code("info"), ", ", _inline_code("warning"), ", ", _inline_code("error"), "."]),
]


_DATA_TYPES = [
    (
        "raw-data",
        "Gzipped FASTQ run files from ENA. Paired-end reads are split from the semicolon-separated fastq_ftp field in the data portal record.",
    ),
    (
        "assemblies",
        ["Gzipped FASTA of every sequence in each assembly, fetched from ENA's browser API ", _inline_code("ena/browser/api/fasta/<acc>.<ver>?download=true&gzip=true"), ". One file per assembly entry on the species record."],
    ),
    (
        "annotations",
        "Ensembl Rapid Release annotation bundles — annotation files, the reference assembly FASTA, and homology files — grouped by assembly name.",
    ),
    (
        "samples-metadata",
        "TSV dump of BioSamples records associated with the selected species. Filtered by --country and -q when provided.",
    ),
]


_EXIT_CODES = [
    ("0", "Success — or dry-run completed."),
    ("1", "One or more files failed after retries."),
    ("2", "Invalid arguments."),
    ("3", "BE unreachable or pagination aborted (e.g. result set exceeds the 10 000-record ceiling)."),
]


layout = html.Div(
    [
        # Header
        dbc.Container(
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            html.H1(
                                "Bulk Download",
                                style={
                                    "fontFamily": "var(--font-display)",
                                    "fontSize": "2.5rem",
                                    "color": "var(--aegis-text-primary)",
                                    "marginBottom": "0.5rem",
                                },
                            ),
                            html.P(
                                [
                                    _inline_code("aegis-download"),
                                    " — a Python CLI for bulk-downloading raw reads, assemblies, annotations, and samples metadata from the AEGIS data portal, filtered by data type and phylogeny.",
                                ],
                                style={
                                    "color": "var(--aegis-text-muted)",
                                    "marginBottom": "0",
                                },
                            ),
                        ],
                        className="pt-4 pb-3",
                    ),
                ),
            ),
        ),
        # Info cards
        dbc.Container(
            dbc.Row(
                [
                    dbc.Col(_info_card("Type", "Python CLI"), md=4, className="mb-3"),
                    dbc.Col(_info_card("Source", "github.com/EMBL-EBI-ABC/AEGIS", link=PACKAGE_URL), md=4, className="mb-3"),
                    dbc.Col(_info_card("Python", "≥ 3.12"), md=4, className="mb-3"),
                ],
                className="mb-4",
            ),
        ),
        # Body
        dbc.Container(
            [
                _section_heading("Install"),
                html.P(
                    [
                        "Clone the AEGIS repository and install the ",
                        _inline_code("downloader"),
                        " package in a virtual environment.",
                    ],
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                _code_block(
                    "git clone https://github.com/EMBL-EBI-ABC/AEGIS.git\n"
                    "cd AEGIS/downloader\n"
                    "python -m venv .venv && source .venv/bin/activate\n"
                    "pip install -e ."
                ),
                html.P(
                    [
                        "This installs the ",
                        _inline_code("aegis-download"),
                        " command. Add ",
                        _inline_code('".[dev]"'),
                        " instead of ",
                        _inline_code('"."'),
                        " to also pull in ",
                        _inline_code("pytest"),
                        " for development.",
                    ],
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                _section_heading("Quick start"),
                html.P(
                    "Download both assemblies for one species:",
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                _code_block("aegis-download --tax-id 43171 --type assemblies --output ./aegis-data"),
                html.P(
                    [
                        "Download all annotation bundles for the order ",
                        html.Em("Lepidoptera"),
                        ":",
                    ],
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                _code_block("aegis-download --type annotations --order Lepidoptera --output ./lepidoptera"),
                html.P(
                    [
                        "Preview a filter without downloading anything (writes a manifest only):",
                    ],
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                _code_block("aegis-download --type raw-data --kingdom Animalia --dry-run"),
                _section_heading("Flags"),
                html.Div(
                    dbc.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th("Flag", style={"width": "28%"}),
                                        html.Th("Default", style={"width": "20%"}),
                                        html.Th("Notes"),
                                    ]
                                )
                            ),
                            html.Tbody([_flag_row(flag, default, notes) for flag, default, notes in _FLAG_ROWS]),
                        ],
                        striped=True,
                        bordered=False,
                        hover=True,
                        responsive=True,
                    ),
                    style={
                        "background": "var(--aegis-bg-elevated)",
                        "borderRadius": "var(--radius-md)",
                        "border": "1px solid var(--aegis-border-subtle)",
                        "overflow": "hidden",
                    },
                ),
                _section_heading("Data types"),
                html.Ul(
                    [
                        html.Li(
                            [
                                _inline_code(name),
                                html.Span(" — ", style={"color": "var(--aegis-text-muted)"}),
                                html.Span(desc if isinstance(desc, str) else desc, style={"color": "var(--aegis-text-secondary)"}),
                            ],
                            style={"marginBottom": "0.6rem"},
                        )
                        for name, desc in _DATA_TYPES
                    ],
                    style={"paddingLeft": "1.25rem", "marginBottom": "0"},
                ),
                _section_heading("Output layout"),
                html.P(
                    [
                        "Files are organised under the ",
                        _inline_code("--output"),
                        " directory. Each species gets its own folder named ",
                        _inline_code("<tax_id>_<scientific_name_slug>"),
                        ", containing a ",
                        _inline_code("metadata.json"),
                        " of the full data portal record and subfolders for each requested data type.",
                    ],
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                _code_block(
                    "<output>/\n"
                    "  manifest.tsv\n"
                    "  samples_metadata.tsv          # if samples-metadata is requested\n"
                    "  by_species/\n"
                    "    43171_linaria_vulgaris/\n"
                    "      metadata.json\n"
                    "      raw_data/\n"
                    "        ERR10828371_1.fastq.gz\n"
                    "        ERR10828371_2.fastq.gz\n"
                    "      assemblies/\n"
                    "        GCA_948329855.1.fasta.gz\n"
                    "        GCA_948329865.1.fasta.gz\n"
                    "      annotations/\n"
                    "        daLinVulg1.1/\n"
                    "          <annotation files>"
                ),
                html.P(
                    [
                        "The ",
                        _inline_code("manifest.tsv"),
                        " lists every download task — URL, destination, expected and actual byte count, status — and is updated in place as workers complete. Re-running with ",
                        _inline_code("--resume"),
                        " (the default) skips files already on disk.",
                    ],
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                _section_heading("Exit codes"),
                html.Div(
                    dbc.Table(
                        [
                            html.Thead(html.Tr([html.Th("Code", style={"width": "12%"}), html.Th("Meaning")])),
                            html.Tbody(
                                [
                                    html.Tr(
                                        [
                                            html.Td(_inline_code(code), style={"padding": "0.55rem 0.75rem"}),
                                            html.Td(meaning, style={"padding": "0.55rem 0.75rem", "color": "var(--aegis-text-secondary)"}),
                                        ]
                                    )
                                    for code, meaning in _EXIT_CODES
                                ]
                            ),
                        ],
                        striped=True,
                        bordered=False,
                        hover=True,
                        responsive=True,
                    ),
                    style={
                        "background": "var(--aegis-bg-elevated)",
                        "borderRadius": "var(--radius-md)",
                        "border": "1px solid var(--aegis-border-subtle)",
                        "overflow": "hidden",
                    },
                ),
                _section_heading("Pagination ceiling"),
                html.P(
                    [
                        "The AEGIS backend caps result-set pagination at ",
                        _inline_code("10 000"),
                        " records (Elasticsearch's ",
                        _inline_code("index.max_result_window"),
                        "). If a filter matches more than that, the tool exits with code ",
                        _inline_code("3"),
                        " and a clear message — narrow the filter (for example by adding ",
                        _inline_code("--order"),
                        " or ",
                        _inline_code("--family"),
                        ") and retry.",
                    ],
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                _section_heading("Resources"),
                html.Ul(
                    [
                        html.Li(
                            html.A(
                                "Source code on GitHub ↗",
                                href=PACKAGE_URL,
                                target="_blank",
                                rel="noopener noreferrer",
                                style={"color": "var(--aegis-accent-primary)", "textDecoration": "underline"},
                            ),
                            style={"marginBottom": "0.4rem"},
                        ),
                        html.Li(
                            html.A(
                                "README ↗",
                                href=README_URL,
                                target="_blank",
                                rel="noopener noreferrer",
                                style={"color": "var(--aegis-accent-primary)", "textDecoration": "underline"},
                            ),
                            style={"marginBottom": "0.4rem"},
                        ),
                        html.Li(
                            [
                                "Report issues: ",
                                html.A(
                                    f"{REPO_URL}/issues ↗",
                                    href=f"{REPO_URL}/issues",
                                    target="_blank",
                                    rel="noopener noreferrer",
                                    style={"color": "var(--aegis-accent-primary)", "textDecoration": "underline"},
                                ),
                            ],
                            style={"marginBottom": "0.4rem"},
                        ),
                    ],
                    style={"paddingLeft": "1.25rem"},
                ),
            ],
            className="pb-5",
        ),
    ]
)
