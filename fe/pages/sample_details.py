import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import requests
from dash import html, callback, Output, Input

from .data_portal import return_badge_status

dash.register_page(
    __name__, path_template="/data-portal/<tax_id>/samples/<accession>"
)

BACKEND_URL = "https://aegis-be-1091670130981.europe-west2.run.app"


def layout(tax_id=None, accession=None, **kwargs):
    return dbc.Container(
        [
            # Breadcrumb
            dbc.Row(
                dbc.Col(
                    html.Nav(
                        html.Ol(
                            [
                                html.Li(
                                    html.A(
                                        "Data Portal",
                                        href="/data-portal",
                                        style={
                                            "color": "var(--aegis-accent-primary)",
                                            "textDecoration": "none",
                                        },
                                    ),
                                    className="breadcrumb-item",
                                ),
                                html.Li(
                                    html.A(
                                        id="breadcrumb-species-name",
                                        href=f"/data-portal/{tax_id}",
                                        style={
                                            "color": "var(--aegis-accent-primary)",
                                            "textDecoration": "none",
                                        },
                                    ),
                                    className="breadcrumb-item",
                                ),
                                html.Li(
                                    accession or "",
                                    className="breadcrumb-item active",
                                    style={
                                        "color": "var(--aegis-text-muted)",
                                        "fontFamily": "var(--font-mono)",
                                    },
                                ),
                            ],
                            className="breadcrumb",
                            style={"marginBottom": "0"},
                        ),
                    ),
                    className="pt-4 pb-3",
                ),
            ),
            # Main content wrapped in spinner
            dbc.Spinner(
                html.Div(
                    id="sample-detail-content",
                    **{
                        "data-accession": accession or "",
                        "data-tax_id": tax_id or "",
                    },
                ),
                color="warning",
            ),
        ],
        className="pb-5",
    )


def _make_metadata_card(title, fields, data):
    """Create a metadata card with a title and grid of label-value pairs."""
    items = []
    for label, key, mono in fields:
        value = data.get(key)
        if value is None or value == "":
            display_value = html.Span(
                "\u2014", style={"color": "var(--aegis-text-muted)"}
            )
        else:
            style = {"color": "var(--aegis-text-primary)"}
            if mono:
                style["fontFamily"] = "var(--font-mono)"
            display_value = html.Span(str(value), style=style)

        items.append(
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
                    display_value,
                ],
                style={
                    "padding": "0.75rem",
                    "background": "var(--aegis-bg-elevated)",
                    "borderRadius": "var(--radius-md)",
                },
            )
        )

    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(
                    title,
                    style={
                        "fontFamily": "var(--font-display)",
                        "color": "var(--aegis-text-primary)",
                        "marginBottom": "1rem",
                        "fontSize": "0.85rem",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.05em",
                    },
                ),
                html.Div(
                    items,
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(140px, 1fr))",
                        "gap": "0.75rem",
                    },
                ),
            ]
        ),
        style={
            "background": "var(--aegis-bg-card)",
            "border": "1px solid var(--aegis-border-subtle)",
            "marginBottom": "1rem",
        },
    )


@callback(
    Output("sample-detail-content", "children"),
    Output("breadcrumb-species-name", "children"),
    Input("sample-detail-content", "data-accession"),
    Input("sample-detail-content", "data-tax_id"),
)
def render_sample_detail(accession, tax_id):
    """Fetch sample data and render the detail page."""
    if not accession:
        return html.P("No sample accession provided."), ""

    response = requests.get(
        f"{BACKEND_URL}/samples/{accession}", timeout=30
    )
    if response.status_code != 200:
        return (
            html.Div(
                [
                    html.H4(
                        "Sample not found",
                        style={
                            "fontFamily": "var(--font-display)",
                            "color": "var(--aegis-text-secondary)",
                        },
                    ),
                    html.P(
                        f"Could not load sample {accession}.",
                        style={"color": "var(--aegis-text-muted)"},
                    ),
                ],
                className="text-center py-5",
            ),
            "",
        )

    sample = response.json()
    scientific_name = sample.get("scientificName", "")
    organism_part = sample.get("organismPart", "")
    tracking_system = sample.get("trackingSystem", "")
    derived_from = sample.get("derivedFrom")
    location = sample.get("location")

    children = []

    # --- Header ---
    header_items = [
        html.H2(
            accession,
            style={
                "fontFamily": "var(--font-mono)",
                "color": "var(--aegis-accent-primary)",
                "marginBottom": "0.25rem",
            },
        ),
        html.Div(
            [
                html.Span(
                    scientific_name,
                    style={
                        "fontStyle": "italic",
                        "color": "var(--aegis-text-primary)",
                        "fontSize": "1.1rem",
                    },
                ),
                html.Span(
                    f" \u2014 {organism_part}" if organism_part else "",
                    style={
                        "color": "var(--aegis-text-secondary)",
                        "fontSize": "1.1rem",
                    },
                ),
            ],
            style={"marginBottom": "0.75rem"},
        ),
    ]

    if tracking_system:
        header_items.append(
            html.Div(return_badge_status(tracking_system), style={"marginBottom": "1rem"})
        )

    children.append(
        html.Div(header_items, style={"marginBottom": "1.5rem"})
    )

    # --- derivedFrom link ---
    if derived_from:
        children.append(
            html.Div(
                [
                    html.Span(
                        "Derived from: ",
                        style={
                            "color": "var(--aegis-text-muted)",
                            "fontSize": "0.9rem",
                        },
                    ),
                    html.A(
                        derived_from,
                        href=f"/data-portal/{tax_id}/samples/{derived_from}",
                        style={
                            "color": "var(--aegis-accent-primary)",
                            "textDecoration": "none",
                            "fontFamily": "var(--font-mono)",
                            "fontSize": "0.9rem",
                        },
                    ),
                ],
                style={
                    "marginBottom": "1.5rem",
                    "padding": "0.75rem 1rem",
                    "background": "var(--aegis-bg-elevated)",
                    "borderRadius": "var(--radius-md)",
                    "border": "1px solid var(--aegis-border-subtle)",
                },
            )
        )

    # --- Metadata cards (left) and Map (right) ---
    # Collection fields: (label, key, mono)
    collection_fields = [
        ("Date", "collectionDate", False),
        ("By", "collectedBy", False),
        ("Institution", "collectingInstitution", False),
        ("Project", "projectName", False),
    ]

    specimen_fields = [
        ("Part", "organismPart", False),
        ("Sex", "sex", False),
        ("Lifestage", "lifestage", False),
        ("TOL ID", "tolid", True),
    ]

    # Build location data dict with lat/lon promoted to top level
    location_data = {
        "country": sample.get("country"),
        "locality": sample.get("locality"),
        "habitat": sample.get("habitat"),
        "elevation": sample.get("elevation"),
        "lat": location.get("lat") if location else None,
        "lon": location.get("lon") if location else None,
    }
    location_fields = [
        ("Country", "country", False),
        ("Locality", "locality", False),
        ("Habitat", "habitat", False),
        ("Elevation", "elevation", False),
        ("Lat", "lat", True),
        ("Lon", "lon", True),
    ]

    left_col = dbc.Col(
        [
            _make_metadata_card("Collection", collection_fields, sample),
            _make_metadata_card("Specimen", specimen_fields, sample),
            _make_metadata_card("Location", location_fields, location_data),
        ],
        md=6,
    )

    # Map (right column)
    if location and location.get("lat") is not None and location.get("lon") is not None:
        lat = float(location["lat"])
        lon = float(location["lon"])
        map_component = dl.Map(
            [
                dl.TileLayer(),
                dl.Marker(position=[lat, lon]),
            ],
            center=[lat, lon],
            zoom=12,
            style={
                "height": "100%",
                "minHeight": "400px",
                "borderRadius": "var(--radius-md)",
            },
        )
    else:
        map_component = html.Div(
            [
                html.P(
                    "No location data available",
                    style={
                        "color": "var(--aegis-text-muted)",
                        "textAlign": "center",
                        "paddingTop": "3rem",
                    },
                ),
            ],
            style={
                "height": "100%",
                "minHeight": "400px",
                "background": "var(--aegis-bg-elevated)",
                "borderRadius": "var(--radius-md)",
                "border": "1px solid var(--aegis-border-subtle)",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
            },
        )

    right_col = dbc.Col(
        dbc.Card(
            dbc.CardBody(map_component, style={"padding": "0"}),
            style={
                "background": "var(--aegis-bg-card)",
                "border": "1px solid var(--aegis-border-subtle)",
                "height": "100%",
                "overflow": "hidden",
            },
        ),
        md=6,
    )

    children.append(
        dbc.Row([left_col, right_col], style={"marginBottom": "1.5rem"})
    )

    # --- External links ---
    biosamples_link = html.A(
        [
            html.Span("BioSamples", style={"marginRight": "0.25rem"}),
            html.Span(
                accession,
                style={"fontFamily": "var(--font-mono)", "fontSize": "0.85rem"},
            ),
        ],
        href=f"https://www.ebi.ac.uk/biosamples/samples/{accession}",
        target="_blank",
        style={
            "color": "var(--aegis-accent-primary)",
            "textDecoration": "none",
            "padding": "0.75rem 1.25rem",
            "background": "var(--aegis-bg-elevated)",
            "borderRadius": "var(--radius-md)",
            "border": "1px solid var(--aegis-border-subtle)",
            "display": "inline-flex",
            "alignItems": "center",
            "transition": "border-color 0.2s ease",
        },
    )

    ena_link = html.A(
        [
            html.Span("ENA", style={"marginRight": "0.25rem"}),
            html.Span(
                accession,
                style={"fontFamily": "var(--font-mono)", "fontSize": "0.85rem"},
            ),
        ],
        href=f"https://www.ebi.ac.uk/ena/browser/view/{accession}",
        target="_blank",
        style={
            "color": "var(--aegis-accent-primary)",
            "textDecoration": "none",
            "padding": "0.75rem 1.25rem",
            "background": "var(--aegis-bg-elevated)",
            "borderRadius": "var(--radius-md)",
            "border": "1px solid var(--aegis-border-subtle)",
            "display": "inline-flex",
            "alignItems": "center",
            "transition": "border-color 0.2s ease",
        },
    )

    children.append(
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.Span(
                            "External Links",
                            style={
                                "fontSize": "0.75rem",
                                "color": "var(--aegis-text-muted)",
                                "textTransform": "uppercase",
                                "letterSpacing": "0.05em",
                                "display": "block",
                                "marginBottom": "0.75rem",
                            },
                        ),
                        html.Div(
                            [biosamples_link, ena_link],
                            style={
                                "display": "flex",
                                "flexWrap": "wrap",
                                "gap": "1rem",
                            },
                        ),
                    ]
                ),
            ),
            style={"marginBottom": "2rem"},
        )
    )

    return children, scientific_name
