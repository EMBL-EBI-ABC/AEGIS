import math
from typing import Callable

import dash
import dash_leaflet as dl
import requests
import json
from dash import html, Output, Input, callback, dcc
import dash_bootstrap_components as dbc

PAGE_SIZE = 10
BACKEND_URL = "https://aegis-be-1091670130981.europe-west2.run.app"

from .data_portal import return_badge_status

dash.register_page(__name__, path_template="/data-portal/<tax_id>")


def layout(tax_id=None, **kwargs):
    return dbc.Container(
        [
            # Back navigation
            dbc.Row(
                dbc.Col(
                    html.A(
                        [
                            html.Span("←", style={"marginRight": "0.5rem"}),
                            "Back to Data Portal",
                        ],
                        href="/data-portal",
                        style={
                            "color": "var(--aegis-text-muted)",
                            "textDecoration": "none",
                            "fontSize": "0.9rem",
                            "display": "inline-flex",
                            "alignItems": "center",
                            "transition": "color 0.2s ease",
                        },
                        className="back-link",
                    ),
                    className="pt-4 pb-3",
                ),
            ),
            # Species Summary Card
            dbc.Row(
                dbc.Col(
                    dbc.Spinner(
                        dbc.Card(
                            dbc.CardBody(id="card", key=tax_id),
                            style={
                                "background": "var(--aegis-bg-card)",
                                "border": "1px solid var(--aegis-border-subtle)",
                            },
                        ),
                        color="warning",
                    ),
                    md={"width": 10, "offset": 1},
                )
            ),
            # Tabs Card
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                dbc.Tabs(id="tabs_header", active_tab="metadata_tab"),
                                style={
                                    "background": "var(--aegis-bg-elevated)",
                                    "borderBottom": "1px solid var(--aegis-border-subtle)",
                                    "padding": "0",
                                },
                            ),
                            dbc.CardBody(
                                [
                                    # Status Legend
                                    html.Div(
                                        [
                                            html.Span(
                                                "Status:",
                                                className="text-muted me-2",
                                                style={"fontSize": "0.85rem"},
                                            ),
                                            dbc.Badge(
                                                "Submitted to Biosamples",
                                                pill=True,
                                                color="secondary",
                                                className="me-1",
                                            ),
                                            html.Span(
                                                "→",
                                                className="mx-1",
                                                style={"color": "var(--aegis-text-muted)"},
                                            ),
                                            dbc.Badge(
                                                "Raw Data - Submitted",
                                                pill=True,
                                                color="primary",
                                                className="me-1",
                                            ),
                                            html.Span(
                                                "→",
                                                className="mx-1",
                                                style={"color": "var(--aegis-text-muted)"},
                                            ),
                                            dbc.Badge(
                                                "Assemblies - Submitted",
                                                pill=True,
                                                color="success",
                                            ),
                                        ],
                                        style={
                                            "marginBottom": "1.5rem",
                                            "padding": "0.75rem 1rem",
                                            "background": "var(--aegis-bg-elevated)",
                                            "borderRadius": "var(--radius-md)",
                                            "display": "flex",
                                            "flexWrap": "wrap",
                                            "alignItems": "center",
                                            "gap": "0.25rem",
                                        },
                                    ),
                                    # Tab Content
                                    html.Div(id="tabs_body", className="card-text"),
                                    # Pagination components (one per tab for independent state)
                                    dbc.Pagination(
                                        id="metadata-pagination",
                                        max_value=1,
                                        first_last=True,
                                        previous_next=True,
                                        fully_expanded=False,
                                        className="justify-content-end mt-3",
                                    ),
                                    dbc.Pagination(
                                        id="raw-data-pagination",
                                        max_value=1,
                                        first_last=True,
                                        previous_next=True,
                                        fully_expanded=False,
                                        className="justify-content-end mt-3",
                                    ),
                                    dbc.Pagination(
                                        id="assemblies-pagination",
                                        max_value=1,
                                        first_last=True,
                                        previous_next=True,
                                        fully_expanded=False,
                                        className="justify-content-end mt-3",
                                    ),
                                ],
                                style={"padding": "1.5rem"},
                            ),
                        ],
                        id="tabs_card",
                        style={
                            "background": "var(--aegis-bg-card)",
                            "border": "1px solid var(--aegis-border-subtle)",
                        },
                    ),
                    md={"width": 10, "offset": 1},
                    style={"marginTop": "1rem", "marginBottom": "2rem"},
                )
            ),
            dcc.Store(id="intermediate-value"),
        ]
    )


def return_biosamples_accession_link(accession: str) -> html.A:
    """Create a link to BioSamples."""
    return html.A(
        accession,
        href=f"https://www.ebi.ac.uk/biosamples/samples/{accession}",
        target="_blank",
        style={
            "color": "var(--aegis-accent-primary)",
            "fontFamily": "var(--font-mono)",
            "fontSize": "0.85rem",
        },
    )


def return_ena_accession_link(accession: str) -> html.A:
    """Create a link to ENA."""
    return html.A(
        accession,
        href=f"https://www.ebi.ac.uk/ena/browser/view/{accession}",
        target="_blank",
        style={
            "color": "var(--aegis-accent-primary)",
            "fontFamily": "var(--font-mono)",
            "fontSize": "0.85rem",
        },
    )


def return_ftp_download_link(url: str) -> html.Div:
    """Create FTP download links."""
    links = []
    for i, link in enumerate(url.split(";")):
        link_name = link.split("/")[-1]
        if i > 0:
            links.append(html.Br())
        links.append(
            html.A(
                link_name,
                href=f"https://{link}",
                target="_blank",
                style={
                    "color": "var(--aegis-accent-primary)",
                    "fontFamily": "var(--font-mono)",
                    "fontSize": "0.8rem",
                },
            )
        )
    return html.Div(links)


def return_table(
    column_names: list[str],
    field_names: list[str],
    data: list[dict[str, str]],
    field_function_mapping: dict[str, Callable],
) -> html.Div:
    """Create a styled data table."""
    table_header = [html.Thead(html.Tr([html.Th(value) for value in column_names]))]
    table_body = [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(
                            field_function_mapping[field_name](row[field_name])
                            if field_name in field_function_mapping
                            else row.get(field_name, "—"),
                            style={"color": "var(--aegis-text-secondary)"},
                        )
                        for field_name in field_names
                    ]
                )
                for row in data
            ]
        )
    ]
    table = dbc.Table(
        table_header + table_body,
        striped=True,
        bordered=False,
        hover=True,
        responsive=True,
    )
    return html.Div(
        table,
        style={
            "background": "var(--aegis-bg-elevated)",
            "borderRadius": "var(--radius-md)",
            "border": "1px solid var(--aegis-border-subtle)",
            "overflow": "hidden",
        },
    )


def taxonomy_badge(label: str, value: str, color: str) -> html.Span:
    """Create a taxonomy level badge."""
    return html.Span(
        [
            html.Span(
                label,
                style={
                    "fontSize": "0.7rem",
                    "color": "var(--aegis-text-muted)",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.05em",
                    "marginRight": "0.25rem",
                },
            ),
            dbc.Badge(value, pill=True, color=color),
        ],
        style={"display": "inline-flex", "alignItems": "center"},
    )


def build_sample_hierarchy(samples, tax_id):
    """Group samples by derivedFrom into a parent/child hierarchy."""
    if not samples:
        return html.Div(
            [
                html.P(
                    "No metadata samples available",
                    style={"color": "var(--aegis-text-muted)"},
                ),
            ],
            className="text-center py-4",
        )

    # Index samples by accession
    by_accession = {s["accession"]: s for s in samples}

    # Find root samples (derivedFrom is None/null or not present)
    roots = [s for s in samples if not s.get("derivedFrom")]
    children_map = {}
    for s in samples:
        parent = s.get("derivedFrom")
        if parent:
            children_map.setdefault(parent, []).append(s)

    # If no roots found but samples exist, treat all as roots
    if not roots and samples:
        roots = samples

    def make_sample_row(s):
        accession = s["accession"]
        organism_part = s.get("organismPart", "")
        tracking_system = s.get("trackingSystem")
        country = s.get("country", "")

        detail_parts = []
        if organism_part:
            detail_parts.append(organism_part)
        if country:
            detail_parts.append(country)
        detail_str = " | ".join(detail_parts)

        return html.Div(
            [
                html.Div([
                    html.A(
                        accession,
                        href=f"/data-portal/{tax_id}/samples/{accession}",
                        style={
                            "color": "var(--aegis-accent-primary)",
                            "fontFamily": "var(--font-mono)",
                            "fontSize": "0.8rem",
                            "textDecoration": "none",
                        },
                    ),
                    html.Span(
                        f" \u00b7 {detail_str}",
                        style={
                            "color": "var(--aegis-text-muted)",
                            "fontSize": "0.8rem",
                        },
                    ) if detail_str else None,
                ]),
                return_badge_status(tracking_system) if tracking_system else html.Span(),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "0.5rem",
                "background": "rgba(255,255,255,0.03)",
                "borderRadius": "4px",
                "marginBottom": "0.3rem",
            },
        )

    def build_tree(sample):
        elements = [make_sample_row(sample)]
        children = children_map.get(sample["accession"], [])
        if children:
            child_elements = []
            for child in children:
                child_elements.extend(build_tree(child))
            elements.append(
                html.Div(
                    child_elements,
                    style={
                        "marginLeft": "1.5rem",
                        "borderLeft": "2px solid var(--aegis-border-subtle)",
                        "paddingLeft": "0.75rem",
                        "marginBottom": "0.5rem",
                    },
                )
            )
        return elements

    all_elements = []
    for root in roots:
        all_elements.extend(build_tree(root))

    return html.Div(all_elements)


@callback(
    Output("card", "children"),
    Output("tabs_header", "children"),
    Output("intermediate-value", "data"),
    Input("card", "key"),
    running=[
        (Output("tabs_card", "class_name"), "invisible", "visible"),
    ],
)
def create_data_portal_record(tax_id):
    """Fetch and display species record details."""
    response = requests.get(
        f"{BACKEND_URL}/data_portal/{tax_id}"
    ).json()
    response = response["results"][0]

    # Fetch samples from dedicated endpoint
    samples_response = requests.get(
        f"{BACKEND_URL}/samples?taxId={tax_id}&size=1000"
    ).json()
    samples_list = samples_response.get("results", [])

    # Build header
    children = [
        html.H2(
            response["scientificName"],
            style={
                "fontFamily": "var(--font-display)",
                "fontStyle": "italic",
                "color": "var(--aegis-text-primary)",
                "marginBottom": "0.25rem",
            },
        ),
        html.P(
            response.get("commonName") or "",
            style={
                "fontSize": "1.1rem",
                "color": "var(--aegis-text-muted)",
                "marginBottom": "1.5rem",
            },
        ),
    ]

    # Compute sample stats
    sample_count = len(samples_list)
    countries = sorted(set(
        s.get("country") for s in samples_list if s.get("country")
    ))
    countries_str = ", ".join(countries) if countries else "—"

    # Info grid
    info_items = [
        ("Tax ID", response["taxId"]),
        ("Status", return_badge_status(response["currentStatus"])),
        ("Sample Count", str(sample_count)),
        ("Countries", countries_str),
    ]

    info_grid = html.Div(
        [
            html.Div(
                [
                    html.Span(
                        label,
                        style={
                            "fontSize": "0.75rem",
                            "color": "var(--aegis-text-muted)",
                            "textTransform": "uppercase",
                            "letterSpacing": "0.05em",
                            "display": "block",
                            "marginBottom": "0.25rem",
                        },
                    ),
                    html.Span(
                        value,
                        style={
                            "color": "var(--aegis-text-primary)",
                            "fontFamily": "var(--font-mono)"
                            if label in ("Tax ID", "Sample Count")
                            else "inherit",
                        },
                    ),
                ],
                style={
                    "padding": "1rem",
                    "background": "var(--aegis-bg-elevated)",
                    "borderRadius": "var(--radius-md)",
                },
            )
            for label, value in info_items
        ],
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(150px, 1fr))",
            "gap": "1rem",
            "marginBottom": "1.5rem",
        },
    )

    # Build map from sample locations
    markers = []
    for s in samples_list:
        loc = s.get("location")
        if loc and loc.get("lat") and loc.get("lon"):
            markers.append(
                dl.Marker(
                    position=[loc["lat"], loc["lon"]],
                    children=dl.Tooltip(f"{s['accession']} \u00b7 {s.get('organismPart', '')}"),
                )
            )

    if markers:
        all_positions = [[m.position[0], m.position[1]] for m in markers]
        species_map = dl.Map(
            [dl.TileLayer()] + markers,
            bounds=all_positions if len(all_positions) > 1 else None,
            center=all_positions[0] if len(all_positions) == 1 else [0, 0],
            zoom=10 if len(all_positions) == 1 else 6,
            style={
                "height": "200px",
                "borderRadius": "var(--radius-md)",
                "border": "1px solid var(--aegis-border-subtle)",
            },
        )
    else:
        species_map = html.Div()

    # Combine info grid and map in a row
    summary_row = dbc.Row([
        dbc.Col(info_grid, md=7),
        dbc.Col(species_map, md=5),
    ])
    children.append(summary_row)

    # Taxonomy path
    phylogeny = response.get("phylogeny", {})
    taxonomy_levels = [
        ("Kingdom", phylogeny.get("kingdom"), "primary"),
        ("Phylum", phylogeny.get("phylum"), "secondary"),
        ("Class", phylogeny.get("class"), "success"),
        ("Order", phylogeny.get("order"), "warning"),
        ("Family", phylogeny.get("family"), "danger"),
        ("Genus", phylogeny.get("genus"), "info"),
    ]

    taxonomy_path = html.Div(
        [
            html.Div(
                "Taxonomy",
                style={
                    "fontSize": "0.75rem",
                    "color": "var(--aegis-text-muted)",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.05em",
                    "marginBottom": "0.75rem",
                },
            ),
            html.Div(
                [
                    item
                    for i, (label, value, color) in enumerate(taxonomy_levels)
                    if value
                    for item in (
                        [
                            html.Span(
                                "→",
                                style={
                                    "color": "var(--aegis-text-muted)",
                                    "margin": "0 0.5rem",
                                },
                            )
                        ]
                        if i > 0
                        else []
                    )
                    + [taxonomy_badge(label, value, color)]
                ],
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "alignItems": "center",
                    "gap": "0.25rem",
                },
            ),
        ],
        style={
            "padding": "1rem",
            "background": "var(--aegis-bg-elevated)",
            "borderRadius": "var(--radius-md)",
        },
    )
    children.append(taxonomy_path)

    # Build tabs
    tabs = [
        dbc.Tab(
            label="Metadata",
            tab_id="metadata_tab",
            label_style={"color": "var(--aegis-text-secondary)"},
            active_label_style={"color": "var(--aegis-accent-primary)"},
        )
    ]
    if len(response.get("rawData", [])) > 0:
        tabs.append(
            dbc.Tab(
                label="Raw Data",
                tab_id="raw_data_tab",
                label_style={"color": "var(--aegis-text-secondary)"},
                active_label_style={"color": "var(--aegis-accent-primary)"},
            )
        )
    if len(response.get("assemblies", [])) > 0:
        tabs.append(
            dbc.Tab(
                label="Assemblies",
                tab_id="assemblies_tab",
                label_style={"color": "var(--aegis-text-secondary)"},
                active_label_style={"color": "var(--aegis-accent-primary)"},
            )
        )

    agg_data = {
        "samples": samples_list,
        "rawData": response.get("rawData", []),
        "assemblies": response.get("assemblies", []),
        "tax_id": tax_id,
    }
    return children, tabs, json.dumps(agg_data)


@callback(
    Output("tabs_body", "children"),
    Output("metadata-pagination", "max_value"),
    Output("metadata-pagination", "style"),
    Output("raw-data-pagination", "max_value"),
    Output("raw-data-pagination", "style"),
    Output("assemblies-pagination", "max_value"),
    Output("assemblies-pagination", "style"),
    Input("tabs_header", "active_tab"),
    Input("intermediate-value", "data"),
    Input("metadata-pagination", "active_page"),
    Input("raw-data-pagination", "active_page"),
    Input("assemblies-pagination", "active_page"),
)
def create_tabs(active_tab, agg_data, metadata_page, raw_data_page, assemblies_page):
    """Render tab content based on active tab."""
    agg_data = json.loads(agg_data)

    # Hide pagination for non-active tabs
    hidden_pagination = {"display": "none"}

    if active_tab == "metadata_tab":
        samples = agg_data.get("samples", [])
        tax_id = agg_data.get("tax_id")

        hierarchy = build_sample_hierarchy(samples, tax_id)
        return hierarchy, 1, hidden_pagination, 1, hidden_pagination, 1, hidden_pagination

    elif active_tab == "raw_data_tab":
        raw_data = agg_data.get("rawData", [])
        total = len(raw_data)
        max_pages = max(1, math.ceil(total / PAGE_SIZE))

        page = raw_data_page or 1
        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        paginated_raw_data = raw_data[start:end]

        if not paginated_raw_data:
            return (
                html.Div(
                    [
                        html.Div(
                            "🧬",
                            style={
                                "fontSize": "2rem",
                                "marginBottom": "0.5rem",
                                "opacity": "0.5",
                            },
                        ),
                        html.P(
                            "No raw data available",
                            style={"color": "var(--aegis-text-muted)"},
                        ),
                    ],
                    className="text-center py-4",
                ),
                1,
                hidden_pagination,
                1,
                hidden_pagination,
                1,
                hidden_pagination,
            )

        field_function_mapping: dict[str, Callable] = {
            "run_accession": return_ena_accession_link,
            "sample_accession": return_ena_accession_link,
            "experiment_accession": return_ena_accession_link,
            "study_accession": return_ena_accession_link,
            "fastq_ftp": return_ftp_download_link,
        }
        table = return_table(
            ["Study", "Sample", "Experiment", "Run", "FASTQ Files"],
            ["study_accession", "sample_accession", "experiment_accession", "run_accession", "fastq_ftp"],
            paginated_raw_data,
            field_function_mapping,
        )
        pagination_style = {"display": "flex"} if total > PAGE_SIZE else {"display": "none"}
        return table, 1, hidden_pagination, max_pages, pagination_style, 1, hidden_pagination

    else:  # assemblies_tab
        assemblies = agg_data.get("assemblies", [])
        total = len(assemblies)
        max_pages = max(1, math.ceil(total / PAGE_SIZE))

        page = assemblies_page or 1
        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        paginated_assemblies = assemblies[start:end]

        if not paginated_assemblies:
            return (
                html.Div(
                    [
                        html.Div(
                            "🔧",
                            style={
                                "fontSize": "2rem",
                                "marginBottom": "0.5rem",
                                "opacity": "0.5",
                            },
                        ),
                        html.P(
                            "No assemblies available",
                            style={"color": "var(--aegis-text-muted)"},
                        ),
                    ],
                    className="text-center py-4",
                ),
                1,
                hidden_pagination,
                1,
                hidden_pagination,
                1,
                hidden_pagination,
            )

        field_function_mapping: dict[str, Callable] = {
            "accession": return_ena_accession_link,
            "study_accession": return_ena_accession_link,
            "sample_accession": return_ena_accession_link,
        }
        table = return_table(
            ["Accession", "Assembly Name", "Description", "Study", "Sample", "Version"],
            ["accession", "assembly_name", "description", "study_accession", "sample_accession", "version"],
            paginated_assemblies,
            field_function_mapping,
        )
        pagination_style = {"display": "flex"} if total > PAGE_SIZE else {"display": "none"}
        return table, 1, hidden_pagination, 1, hidden_pagination, max_pages, pagination_style
