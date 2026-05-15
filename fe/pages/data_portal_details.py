import math
from typing import Callable

import dash
import dash_leaflet as dl
import requests
import json
from dash import html, Output, Input, callback, dcc, MATCH
import dash_bootstrap_components as dbc

PAGE_SIZE = 10
import os
BACKEND_URL = os.getenv("BACKEND_URL", "https://portal.aegisearth.bio/api")
ENSEMBL_RAPID_RELEASE_BASE = "https://ftp.ebi.ac.uk/pub/ensemblorganisms"

from .utils import return_badge_status

dash.register_page(__name__, path_template="/data-portal/<tax_id>", order=1)


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
                            "textDecoration": "underline",
                            "textUnderlineOffset": "3px",
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
                            dbc.CardBody(
                                [
                                    dbc.Row([
                                        dbc.Col(html.Div(id="card", key=tax_id), md=7),
                                        dbc.Col(
                                            dl.Map(
                                                [
                                                    dl.TileLayer(
                                                        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
                                                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                                                    ),
                                                    dl.LayerGroup(id="species-map-markers"),
                                                ],
                                                id="species-map",
                                                center=[52, 0],
                                                zoom=5,
                                                style={
                                                    "height": "250px",
                                                    "borderRadius": "var(--radius-md)",
                                                    "border": "1px solid var(--aegis-border-subtle)",
                                                },
                                            ),
                                            md=5,
                                        ),
                                    ]),
                                    html.Div(id="taxonomy-row"),
                                ],
                            ),
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
                                                color="info",
                                                className="me-1",
                                            ),
                                            html.Span(
                                                "→",
                                                className="mx-1",
                                                style={"color": "var(--aegis-text-muted)"},
                                            ),
                                            dbc.Badge(
                                                "Annotation Complete",
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


_EXTERNAL_ARROW_STYLE = {
    "fontSize": "0.85em",
    "fontFamily": "var(--font-body)",
}


def _external_anchor(label: str, href: str, *, mono: bool = True, font_size: str = "0.85rem") -> html.A:
    """Internal helper: external link styled with underline + ↗ glyph.

    Wraps the arrow in a `display: inline` span (not inline-block) so the line layout
    treats label+arrow as one inline run — no extra break opportunity is introduced
    between them. Hyphens inside long file-name labels remain natural wrap points.
    """
    style = {
        "color": "var(--aegis-accent-primary)",
        "fontSize": font_size,
        "textDecoration": "underline",
        "textUnderlineOffset": "3px",
    }
    if mono:
        style["fontFamily"] = "var(--font-mono)"
    return html.A(
        [label, html.Span(" ↗", style=_EXTERNAL_ARROW_STYLE)],
        href=href,
        target="_blank",
        rel="noopener noreferrer",
        style=style,
    )


def return_biosamples_accession_link(accession: str) -> html.A:
    """Create a link to BioSamples."""
    return _external_anchor(accession, f"https://www.ebi.ac.uk/biosamples/samples/{accession}")


def return_ena_accession_link(accession: str) -> html.A:
    """Create a link to ENA."""
    return _external_anchor(accession, f"https://www.ebi.ac.uk/ena/browser/view/{accession}")


def return_ftp_download_link(url: str) -> html.Div:
    """Create FTP download links."""
    links = []
    for i, link in enumerate(url.split(";")):
        link_name = link.split("/")[-1]
        if i > 0:
            links.append(html.Br())
        links.append(
            _external_anchor(link_name, f"https://{link}", font_size="0.8rem")
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


def _annotation_file_section(title: str, files: list[dict]) -> html.Div | None:
    """Render one of the three file lists on an annotation card. Returns None if empty."""
    if not files:
        return None
    by_category: dict[str, list[dict]] = {}
    for f in files:
        by_category.setdefault(f.get("category") or "files", []).append(f)

    blocks = [
        html.Div(
            title,
            style={
                "fontSize": "0.75rem",
                "fontWeight": "600",
                "color": "var(--aegis-text-secondary)",
                "textTransform": "uppercase",
                "letterSpacing": "0.05em",
                "marginBottom": "0.5rem",
            },
        ),
    ]
    for category, entries in by_category.items():
        blocks.append(
            html.Div(
                category,
                style={
                    "fontSize": "0.7rem",
                    "color": "var(--aegis-text-muted)",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.05em",
                    "marginTop": "0.5rem",
                    "marginBottom": "0.25rem",
                },
            )
        )
        for entry in entries:
            name = entry.get("name") or entry.get("path", "").split("/")[-1]
            path = entry.get("path", "")
            blocks.append(
                html.Div(
                    _external_anchor(name, f"{ENSEMBL_RAPID_RELEASE_BASE}/{path}", font_size="0.85rem"),
                    style={"marginLeft": "0.75rem", "marginBottom": "0.25rem"},
                )
            )

    return html.Div(
        blocks,
        style={
            "padding": "1rem",
            "background": "var(--aegis-bg-elevated)",
            "borderRadius": "var(--radius-md)",
            "border": "1px solid var(--aegis-border-subtle)",
        },
    )


def _reference_specimen_link(biosample_id: str, sample_accessions: set, tax_id) -> html.A:
    """Internal portal link when the biosample is in our index, BioSamples fallback otherwise."""
    if biosample_id in sample_accessions:
        return html.A(
            biosample_id,
            href=f"/data-portal/{tax_id}/samples/{biosample_id}",
            style={
                "color": "var(--aegis-accent-primary)",
                "fontFamily": "var(--font-mono)",
                "fontSize": "0.9rem",
                "textDecoration": "underline",
                "textUnderlineOffset": "3px",
            },
        )
    return return_biosamples_accession_link(biosample_id)


def _annotation_card(annotation: dict, sample_accessions: set, tax_id) -> html.Div:
    """Render one annotation entry as a card with header, reference specimen, and file lists."""
    assembly_name = annotation.get("assemblyName") or "—"
    assembly_accession = annotation.get("assemblyAccession") or "—"
    provider = annotation.get("provider") or "—"
    release = annotation.get("release") or ""
    strain = annotation.get("strain")
    biosample = annotation.get("biosampleId")

    header_parts = [
        html.Span(
            assembly_name,
            style={"fontFamily": "var(--font-mono)", "fontWeight": "600"},
        ),
        html.Span(f" ({assembly_accession})", style={"color": "var(--aegis-text-muted)"}),
        html.Span(" — "),
        html.Span(provider, style={"color": "var(--aegis-accent-primary)", "fontWeight": "500"}),
        html.Span(f" {release}".rstrip(), style={"color": "var(--aegis-text-secondary)"}),
    ]

    meta_rows = []
    if biosample:
        meta_rows.append(
            html.Div(
                [
                    html.Span(
                        "Reference specimen: ",
                        style={"color": "var(--aegis-text-muted)", "fontSize": "0.85rem"},
                    ),
                    _reference_specimen_link(biosample, sample_accessions, tax_id),
                ],
                style={"marginBottom": "0.4rem"},
            )
        )
    if strain and strain != "reference":
        meta_rows.append(
            html.Div(
                [
                    html.Span(
                        "Strain: ",
                        style={"color": "var(--aegis-text-muted)", "fontSize": "0.85rem"},
                    ),
                    html.Span(strain, style={"color": "var(--aegis-text-primary)", "fontSize": "0.85rem"}),
                ],
                style={"marginBottom": "0.4rem"},
            )
        )

    sections = [
        _annotation_file_section("Annotation files", annotation.get("annotationFiles") or []),
        _annotation_file_section("Genome / assembly files", annotation.get("assemblyFiles") or []),
        _annotation_file_section("Homology files", annotation.get("homologyFiles") or []),
    ]
    sections = [s for s in sections if s is not None]

    return html.Div(
        [
            html.Div(header_parts, style={"fontSize": "1rem", "marginBottom": "0.75rem"}),
            *meta_rows,
            html.Div(
                sections,
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))",
                    "gap": "0.75rem",
                    "marginTop": "0.75rem",
                },
            ),
        ],
        style={
            "padding": "1.25rem",
            "background": "var(--aegis-bg-card)",
            "border": "1px solid var(--aegis-border-subtle)",
            "borderRadius": "var(--radius-md)",
            "marginBottom": "1rem",
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

    def _format_sex(sex_value):
        if not sex_value:
            return None
        lower = sex_value.lower()
        if lower == "female":
            return html.Span("♀", title="Female", style={"fontSize": "1rem"})
        elif lower == "male":
            return html.Span("♂", title="Male", style={"fontSize": "1rem"})
        return html.Span(sex_value, style={"fontSize": "0.8rem"})

    def _sample_detail_parts(s):
        """Return list of components for sample detail display."""
        parts = []
        if s.get("organismPart"):
            parts.append(html.Span(s["organismPart"]))
        sex_el = _format_sex(s.get("sex"))
        if sex_el:
            parts.append(sex_el)
        return parts

    def make_sample_link(s):
        return html.A(
            s["accession"],
            href=f"/data-portal/{tax_id}/samples/{s['accession']}",
            style={
                "color": "var(--aegis-accent-primary)",
                "fontFamily": "var(--font-mono)",
                "fontSize": "0.8rem",
                "textDecoration": "underline",
                "textUnderlineOffset": "3px",
            },
        )

    def make_child_row(s):
        detail_parts = _sample_detail_parts(s)
        left = [make_sample_link(s)]
        for part in detail_parts:
            left.append(html.Span(" \u00b7 ", style={"color": "var(--aegis-text-muted)", "fontSize": "0.8rem"}))
            left.append(html.Span(part, style={"color": "var(--aegis-text-muted)", "fontSize": "0.8rem"}))
        return html.Div(
            [
                html.Div(left),
                return_badge_status(s.get("trackingSystem", "")) if s.get("trackingSystem") else html.Span(),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "0.4rem 0.5rem",
                "borderBottom": "1px solid rgba(255,255,255,0.03)",
            },
        )

    all_elements = []
    for i, root in enumerate(roots):
        accession = root["accession"]
        detail_parts = _sample_detail_parts(root)
        children = children_map.get(accession, [])
        collapse_id = {"type": "sample-collapse", "index": i}
        toggle_id = {"type": "sample-toggle", "index": i}

        # Root row
        left_items = [make_sample_link(root)]
        for part in detail_parts:
            left_items.append(html.Span(" \u00b7 ", style={"color": "var(--aegis-text-muted)", "fontSize": "0.8rem"}))
            left_items.append(html.Span(part, style={"color": "var(--aegis-text-muted)", "fontSize": "0.8rem"}))

        right_items = []
        if children:
            chevron_id = {"type": "sample-chevron", "index": i}
            right_items.append(
                html.Span(
                    [
                        html.Span(
                            "▸",
                            id=chevron_id,
                            style={
                                "fontSize": "1.15rem",
                                "lineHeight": "1",
                                "marginRight": "0.4rem",
                            },
                        ),
                        f"+{len(children)} derived",
                    ],
                    id=toggle_id,
                    n_clicks=0,
                    style={
                        "color": "var(--aegis-accent-primary)",
                        "fontSize": "0.75rem",
                        "fontWeight": "500",
                        "cursor": "pointer",
                        "marginRight": "0.75rem",
                        "background": "var(--aegis-accent-soft)",
                        "border": "1px solid var(--aegis-border-accent)",
                        "padding": "0.15rem 0.55rem",
                        "borderRadius": "4px",
                        "userSelect": "none",
                        "display": "inline-flex",
                        "alignItems": "center",
                    },
                ),
            )
        right_items.append(
            return_badge_status(root.get("trackingSystem", "")) if root.get("trackingSystem") else html.Span()
        )

        root_row = html.Div(
            [
                html.Div(left_items),
                html.Div(right_items, style={"display": "flex", "alignItems": "center"}),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "0.5rem",
                "background": "var(--aegis-bg-elevated)",
                "borderRadius": "4px",
                "marginBottom": "0.3rem",
            },
        )
        all_elements.append(root_row)

        # Collapsible children
        if children:
            child_rows = [make_child_row(c) for c in children]
            all_elements.append(
                dbc.Collapse(
                    html.Div(
                        child_rows,
                        style={
                            "marginLeft": "1.5rem",
                            "borderLeft": "2px solid var(--aegis-border-subtle)",
                            "paddingLeft": "0.75rem",
                            "marginBottom": "0.5rem",
                        },
                    ),
                    id=collapse_id,
                    is_open=False,
                )
            )

    return html.Div(all_elements)


@callback(
    Output({"type": "sample-collapse", "index": MATCH}, "is_open"),
    Input({"type": "sample-toggle", "index": MATCH}, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_sample_children(n_clicks):
    """Toggle visibility of derived samples."""
    if n_clicks:
        return n_clicks % 2 == 1
    return False


@callback(
    Output({"type": "sample-chevron", "index": MATCH}, "children"),
    Input({"type": "sample-collapse", "index": MATCH}, "is_open"),
)
def update_chevron(is_open):
    """Rotate the chevron to reflect the collapse state."""
    return "▾" if is_open else "▸"


@callback(
    Output("card", "children"),
    Output("tabs_header", "children"),
    Output("intermediate-value", "data"),
    Output("species-map-markers", "children"),
    Output("taxonomy-row", "children"),
    Output("species-map", "viewport"),
    Input("card", "key"),
    running=[
        (Output("tabs_card", "class_name"), "invisible", "visible"),
    ],
)
def create_data_portal_record(tax_id):
    """Fetch and display species record details."""
    if not tax_id:
        return [], [], json.dumps({"samples": [], "rawData": [], "assemblies": [], "tax_id": None}), [], html.Div(), dash.no_update
    response = requests.get(
        f"{BACKEND_URL}/data_portal/{tax_id}"
    ).json()
    if not response.get("results"):
        return [], [], json.dumps({"samples": [], "rawData": [], "assemblies": [], "tax_id": tax_id}), [], html.Div(), dash.no_update
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

    # Build map markers — deduplicate by position, show count
    location_groups = {}
    for s in samples_list:
        loc = s.get("location")
        if loc and loc.get("lat") and loc.get("lon"):
            key = (loc["lat"], loc["lon"])
            location_groups.setdefault(key, []).append(s)

    map_markers = []
    for (lat, lon), group in location_groups.items():
        count = len(group)
        if count == 1:
            s = group[0]
            tooltip_text = f"{s['accession']} \u00b7 {s.get('organismPart', '')}"
        else:
            tooltip_text = f"{count} samples"
        map_markers.append(
            dl.CircleMarker(
                center=[lat, lon],
                radius=max(8, min(30, count / 2)),
                children=dl.Tooltip(tooltip_text),
                color="#4E6B66",
                fillColor="#4E6B66",
                fillOpacity=0.7,
            )
        )

    children.append(info_grid)

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
    # taxonomy_path rendered in taxonomy-row (full width, outside the md=7 column)

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
    if len(response.get("annotations") or []) > 0:
        tabs.append(
            dbc.Tab(
                label="Annotations",
                tab_id="annotations_tab",
                label_style={"color": "var(--aegis-text-secondary)"},
                active_label_style={"color": "var(--aegis-accent-primary)"},
            )
        )

    agg_data = {
        "samples": samples_list,
        "rawData": response.get("rawData", []),
        "assemblies": response.get("assemblies", []),
        "annotations": response.get("annotations") or [],
        "tax_id": tax_id,
    }
    # Compute map viewport to fit all marker positions
    if location_groups:
        all_lats = [lat for lat, lon in location_groups]
        all_lons = [lon for lat, lon in location_groups]
        if len(location_groups) == 1:
            map_viewport = {"center": [all_lats[0], all_lons[0]], "zoom": 10}
        else:
            center_lat = (min(all_lats) + max(all_lats)) / 2
            center_lon = (min(all_lons) + max(all_lons)) / 2
            map_viewport = {"center": [center_lat, center_lon], "zoom": 6}
    else:
        map_viewport = dash.no_update

    return children, tabs, json.dumps(agg_data), map_markers, taxonomy_path, map_viewport


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
    if not agg_data:
        return html.Div(), 1, {"display": "none"}, 1, {"display": "none"}, 1, {"display": "none"}
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

    elif active_tab == "assemblies_tab":
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

    else:  # annotations_tab
        annotations = agg_data.get("annotations") or []
        tax_id = agg_data.get("tax_id")
        sample_accessions = {s["accession"] for s in agg_data.get("samples", []) if s.get("accession")}

        if not annotations:
            return (
                html.Div(
                    [
                        html.Div(
                            "📑",
                            style={
                                "fontSize": "2rem",
                                "marginBottom": "0.5rem",
                                "opacity": "0.5",
                            },
                        ),
                        html.P(
                            "No annotations available",
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

        cards = [_annotation_card(a, sample_accessions, tax_id) for a in annotations]
        return html.Div(cards), 1, hidden_pagination, 1, hidden_pagination, 1, hidden_pagination
