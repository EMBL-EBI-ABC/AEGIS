import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import requests
from dash import html, dcc, callback, Output, Input

from .utils import return_badge_status

dash.register_page(
    __name__,
    path_template="/data-portal/<tax_id>/samples/<accession>",
    order=0,
)

import os
BACKEND_URL = os.getenv("BACKEND_URL", "https://aegis-be-1091670130981.europe-west2.run.app")


def layout(tax_id=None, accession=None, **kwargs):
    return dbc.Container(
        [
            # Breadcrumb
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            html.A(
                                "Data Portal",
                                href="/data-portal",
                                style={"color": "var(--aegis-accent-primary)", "textDecoration": "none", "fontSize": "0.85rem"},
                            ),
                            html.Span(" → ", style={"color": "var(--aegis-text-muted)", "margin": "0 0.4rem", "fontSize": "0.85rem"}),
                            html.A(
                                id="breadcrumb-species-name",
                                href=f"/data-portal/{tax_id}",
                                style={"color": "var(--aegis-accent-primary)", "textDecoration": "none", "fontStyle": "italic", "fontSize": "0.85rem"},
                            ),
                            html.Span(" → ", style={"color": "var(--aegis-text-muted)", "margin": "0 0.4rem", "fontSize": "0.85rem"}),
                            html.Span(
                                accession or "",
                                style={"color": "var(--aegis-text-muted)", "fontFamily": "var(--font-mono)", "fontSize": "0.85rem"},
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center"},
                    ),
                    className="pt-4 pb-3",
                ),
            ),
            # Stores for passing URL params to callback
            dcc.Store(id="sample-accession-store", data=accession),
            dcc.Store(id="sample-taxid-store", data=tax_id),
            # Main content wrapped in spinner
            dbc.Spinner(
                html.Div(id="sample-detail-content"),
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
            continue
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
    Input("sample-accession-store", "data"),
    Input("sample-taxid-store", "data"),
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

    data = response.json()
    if not data.get("results"):
        return html.P("Sample not found.", style={"color": "var(--aegis-text-muted)"}), ""
    sample = data["results"][0]
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

    # Status badge + external links row
    badge_and_links = []
    if tracking_system:
        badge_and_links.append(return_badge_status(tracking_system))

    link_style = {
        "color": "var(--aegis-accent-primary)",
        "textDecoration": "none",
        "padding": "0.3rem 0.75rem",
        "background": "var(--aegis-bg-elevated)",
        "borderRadius": "var(--radius-md)",
        "border": "1px solid var(--aegis-border-subtle)",
        "fontSize": "0.8rem",
        "display": "inline-flex",
        "alignItems": "center",
    }
    badge_and_links.append(
        html.A("BioSamples", href=f"https://www.ebi.ac.uk/biosamples/samples/{accession}", target="_blank", style=link_style)
    )
    badge_and_links.append(
        html.A("ENA", href=f"https://www.ebi.ac.uk/ena/browser/view/{accession}", target="_blank", style=link_style)
    )
    header_items.append(
        html.Div(badge_and_links, style={"display": "flex", "gap": "0.5rem", "alignItems": "center", "flexWrap": "wrap"})
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
    location_data = {
        "country": sample.get("country"),
        "locality": sample.get("locality"),
        "habitat": sample.get("habitat"),
        "elevation": f"{sample['elevation']}m" if sample.get("elevation") is not None else None,
        "depth": f"{sample['depth']}m" if sample.get("depth") is not None else None,
        "lat": location.get("lat") if location else None,
        "lon": location.get("lon") if location else None,
    }

    original_location_data = {
        "originalCollectionDate": sample.get("originalCollectionDate"),
        "originalGeographicLocation": sample.get("originalGeographicLocation"),
        "originalLatitude": sample.get("originalLatitude"),
        "originalLongitude": sample.get("originalLongitude"),
    }

    # Build cards — only show cards that have at least one non-null value
    def _card_if_has_data(title, fields, data):
        if any(data.get(key) is not None for _, key, _ in fields):
            return _make_metadata_card(title, fields, data)
        return None

    cards = [
        _make_metadata_card("Collection", [
            ("Date", "collectionDate", False),
            ("Collected By", "collectedBy", False),
            ("Institution", "collectingInstitution", False),
            ("GAL", "gal", False),
            ("Project", "projectName", False),
            ("Method", "sampleCollectionMethod", False),
        ], sample),
        _make_metadata_card("Specimen", [
            ("Part", "organismPart", False),
            ("Sex", "sex", False),
            ("Lifestage", "lifestage", False),
            ("TOL ID", "tolid", True),
            ("Specimen ID", "specimenId", True),
            ("Specimen Voucher", "specimenVoucher", True),
        ], sample),
        _make_metadata_card("Location", [
            ("Country", "country", False),
            ("Locality", "locality", False),
            ("Habitat", "habitat", False),
            ("Elevation", "elevation", False),
            ("Depth", "depth", False),
            ("Lat", "lat", True),
            ("Lon", "lon", True),
        ], location_data),
        _card_if_has_data("Identification", [
            ("Identified By", "identifiedBy", False),
            ("Identifier Affiliation", "identifierAffiliation", False),
            ("Sample Coordinator", "sampleCoordinator", False),
            ("Coordinator Affiliation", "sampleCoordinatorAffiliation", False),
            ("Barcoding Center", "barcodingCenter", False),
        ], sample),
        _card_if_has_data("Relationships", [
            ("Derived From", "derivedFrom", True),
            ("Symbiont Of", "sampleSymbiontOf", True),
            ("Symbiont", "symbiont", False),
            ("Relationship", "relationship", False),
            ("Same As", "sampleSameAs", True),
        ], sample),
        _card_if_has_data("Original Location", [
            ("Date", "originalCollectionDate", False),
            ("Location", "originalGeographicLocation", False),
            ("Lat", "originalLatitude", True),
            ("Lon", "originalLongitude", True),
        ], original_location_data),
    ]
    # Filter out None cards (those with no data)
    cards = [c for c in cards if c is not None]

    # Custom fields table
    custom_fields = sample.get("customFields") or []
    if custom_fields:
        rows = [
            html.Tr([
                html.Td(
                    cf.get("key", ""),
                    style={"color": "var(--aegis-text-muted)", "fontSize": "0.85rem", "padding": "0.4rem 0.75rem"},
                ),
                html.Td(
                    cf.get("value", ""),
                    style={"color": "var(--aegis-text-primary)", "fontSize": "0.85rem", "padding": "0.4rem 0.75rem"},
                ),
            ])
            for cf in custom_fields
        ]
        cards.append(
            dbc.Card(
                dbc.CardBody([
                    html.H6(
                        "Custom Fields",
                        style={
                            "fontFamily": "var(--font-display)",
                            "color": "var(--aegis-text-primary)",
                            "marginBottom": "1rem",
                            "fontSize": "0.85rem",
                            "textTransform": "uppercase",
                            "letterSpacing": "0.05em",
                        },
                    ),
                    dbc.Table(
                        [html.Tbody(rows)],
                        striped=True, bordered=False, hover=True, responsive=True,
                        style={"marginBottom": "0"},
                    ),
                ]),
                style={
                    "background": "var(--aegis-bg-card)",
                    "border": "1px solid var(--aegis-border-subtle)",
                    "marginBottom": "1rem",
                },
            )
        )

    # Map (full width, on top)
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
                "height": "300px",
                "borderRadius": "var(--radius-md)",
            },
        )
        children.append(
            dbc.Card(
                dbc.CardBody(map_component, style={"padding": "0"}),
                style={
                    "background": "var(--aegis-bg-card)",
                    "border": "1px solid var(--aegis-border-subtle)",
                    "overflow": "hidden",
                    "marginBottom": "1rem",
                },
            )
        )

    # Cards in two columns
    left_cards = cards[::2]   # even indices
    right_cards = cards[1::2]  # odd indices
    children.append(
        dbc.Row(
            [
                dbc.Col(left_cards, md=6),
                dbc.Col(right_cards, md=6),
            ],
            style={"marginBottom": "1.5rem"},
        )
    )

    return children, scientific_name
