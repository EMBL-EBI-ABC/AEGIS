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
BACKEND_URL = os.getenv("BACKEND_URL", "https://portal.aegisearth.bio/api")


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


def _is_component(value):
    """True if value is a Dash component (rather than a primitive)."""
    return not isinstance(value, (str, int, float, bool, list))


def _has_value(value):
    """True if value should render — non-empty primitive, non-empty list, or component."""
    if value is None or value == "":
        return False
    if isinstance(value, list) and not value:
        return False
    return True


def _format_date(value):
    """Normalize an ES date string to YYYY-MM-DD.

    ES may return dates as plain 'YYYY-MM-DD' or as ISO 8601
    ('YYYY-MM-DDTHH:MM:SS...'); we just slice the ISO prefix.
    """
    if value is None or value == "":
        return None
    text = str(value)
    return text[:10] if len(text) >= 10 else text


def _date_or_text(date_value, text_value):
    """Return the date if present, otherwise the text token in italics, otherwise None.

    Used for ERC000053 fields where the date may be missing but the source
    provides an allowed-missing token (e.g. 'not provided', 'restricted access').
    """
    if date_value:
        return date_value
    if text_value:
        return html.Em(
            str(text_value),
            style={"color": "var(--aegis-text-secondary)"},
        )
    return None


def _external_link(value, href, mono=False):
    """Render an external clickable anchor opening in a new tab.

    Uses a visible underline + trailing ↗ glyph so the affordance reads
    clearly even when the surrounding metadata row uses colored 'data'
    text. Colour comes from the global a rule so :hover can re-tint.
    """
    style = {
        "textDecoration": "underline",
        "textUnderlineOffset": "3px",
    }
    if mono:
        style["fontFamily"] = "var(--font-mono)"
    return html.A(
        [
            str(value),
            html.Span(
                "↗",  # ↗ NORTH EAST ARROW — universally reads as "external"
                style={
                    "fontSize": "0.8em",
                    "marginLeft": "0.25em",
                    "fontFamily": "var(--font-body)",
                    "textDecoration": "none",
                    "display": "inline-block",
                },
            ),
        ],
        href=href,
        target="_blank",
        rel="noopener noreferrer",
        style=style,
    )


def _make_metadata_card(title, fields, data, sample_link_fields=None, tax_id=None):
    """Create a metadata card with a title and grid of label-value pairs.

    Each field is (label, key, mono). data[key] may be:
      - None / "" / empty list  -> row hidden
      - list of strings         -> joined with "; "
      - Dash component          -> rendered as-is (allows italics, links, etc.)
      - str / int / float       -> rendered as text

    sample_link_fields: set of field keys whose values are BioSample accessions
    and should render as links to the sample detail page.
    """
    items = []
    for label, key, mono in fields:
        value = data.get(key)
        if not _has_value(value):
            continue

        if isinstance(value, list):
            value = "; ".join(str(v) for v in value if v is not None and v != "")
            if not value:
                continue

        style = {"color": "var(--aegis-text-primary)"}
        if mono:
            style["fontFamily"] = "var(--font-mono)"
        if sample_link_fields and key in sample_link_fields and tax_id and not _is_component(value):
            display_value = html.A(
                str(value),
                href=f"/data-portal/{tax_id}/samples/{value}",
                style={
                    "color": "var(--aegis-accent-primary)",
                    "textDecoration": "none",
                    "fontFamily": "var(--font-mono)",
                },
            )
        elif _is_component(value):
            display_value = value
        else:
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
    common_name = sample.get("commonName") or ""
    organism_part = sample.get("organismPart") or ""
    tracking_system = sample.get("trackingSystem", "")
    derived_from = sample.get("derivedFrom")
    location = sample.get("location")

    children = []

    # --- Header ---
    name_lines = []
    if scientific_name:
        name_lines.append(
            html.Div(
                scientific_name,
                style={
                    "fontStyle": "italic",
                    "color": "var(--aegis-text-primary)",
                    "fontSize": "1.15rem",
                    "lineHeight": "1.3",
                },
            )
        )
    if common_name:
        name_lines.append(
            html.Div(
                common_name,
                style={
                    "color": "var(--aegis-text-secondary)",
                    "fontSize": "1rem",
                    "lineHeight": "1.3",
                },
            )
        )
    if organism_part:
        name_lines.append(
            html.Div(
                organism_part,
                style={
                    "color": "var(--aegis-text-muted)",
                    "fontSize": "0.8rem",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.05em",
                    "marginTop": "0.25rem",
                },
            )
        )

    header_items = [
        html.H2(
            accession,
            style={
                "fontFamily": "var(--font-mono)",
                "color": "var(--aegis-accent-primary)",
                "marginBottom": "0.25rem",
            },
        ),
        html.Div(name_lines, style={"marginBottom": "0.75rem"}),
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

    # --- Build display data ---
    # Start from the sample dict and overlay derived/formatted values.
    display = dict(sample)
    display["collectionDate"] = _date_or_text(
        _format_date(sample.get("collectionDate")), sample.get("collectionDateText")
    )
    display["originalCollectionDate"] = _date_or_text(
        _format_date(sample.get("originalCollectionDate")),
        sample.get("originalCollectionDateText"),
    )
    display["insdcFirstPublic"] = _format_date(sample.get("insdcFirstPublic"))
    display["insdcLastUpdate"] = _format_date(sample.get("insdcLastUpdate"))
    if sample.get("elevation") is not None:
        display["elevation"] = f"{sample['elevation']}m"
    if sample.get("depth") is not None:
        display["depth"] = f"{sample['depth']}m"
    display["lat"] = location.get("lat") if location else None
    display["lon"] = location.get("lon") if location else None

    # Pre-build link components for Provenance.
    if sample.get("sraAccession"):
        display["sraAccession"] = _external_link(
            sample["sraAccession"],
            f"https://www.ncbi.nlm.nih.gov/sra/{sample['sraAccession']}",
            mono=True,
        )

    # Build cards — only show conditional cards that have at least one value
    def _card_if_has_data(title, fields, data, **kwargs):
        if any(_has_value(data.get(key)) for _, key, _ in fields):
            return _make_metadata_card(title, fields, data, **kwargs)
        return None

    # Order matters — fixed by spec:
    # Collection, Specimen, Location, Identification, Relationships, Custom Fields,
    # then the new conditional boxes (Origin, Marine Event, Provenance).
    core_cards = [
        _make_metadata_card("Collection", [
            ("Date", "collectionDate", False),
            ("Collected By", "collectedBy", False),
            ("Institution", "collectingInstitution", False),
            ("GAL", "gal", False),
            ("Project Tag", "projectTag", False),
            ("Project Name", "projectName", False),
            ("Method", "sampleCollectionMethod", False),
            ("Sample Coordinator", "sampleCoordinator", False),
            ("Coordinator Affiliation", "sampleCoordinatorAffiliation", False),
            ("Barcoding Center", "barcodingCenter", False),
        ], display),
        _make_metadata_card("Specimen", [
            ("Part", "organismPart", False),
            ("Sex", "sex", False),
            ("Lifestage", "lifestage", False),
            ("TOL ID", "tolid", True),
            ("Specimen ID", "specimenId", True),
            ("Specimen Voucher", "specimenVoucher", True),
            ("GAL Sample ID", "galSampleId", True),
            ("Bio Material", "bioMaterial", False),
            ("Proxy Voucher", "proxyVoucher", True),
            ("Proxy Biomaterial", "proxyBiomaterial", False),
            ("Culture / Strain ID", "cultureOrStrainId", True),
        ], display),
        _make_metadata_card("Location", [
            ("Country", "country", False),
            ("Locality", "locality", False),
            ("Habitat", "habitat", False),
            ("Elevation", "elevation", False),
            ("Depth", "depth", False),
            ("Lat", "lat", True),
            ("Lon", "lon", True),
        ], display),
        _card_if_has_data("Identification", [
            ("Identified By", "identifiedBy", False),
            ("Identifier Affiliation", "identifierAffiliation", False),
        ], display),
        _card_if_has_data("Relationships", [
            ("Relationship", "relationship", False),
            ("Symbiont Of", "sampleSymbiontOf", True),
            ("Symbiont", "symbiont", False),
            ("Derived From", "derivedFrom", True),
            ("Same As", "sampleSameAs", True),
        ], display, sample_link_fields={"derivedFrom", "sampleSymbiontOf", "sampleSameAs"}, tax_id=tax_id),
    ]
    extra_cards = [
        _card_if_has_data("Origin", [
            ("Original Date", "originalCollectionDate", False),
            ("Original Location", "originalGeographicLocation", False),
            ("Original Lat", "originalLatitude", True),
            ("Original Lon", "originalLongitude", True),
        ], display),
        _card_if_has_data("Marine Event", [
            ("Lat Start", "latitudeStart", True),
            ("Lon Start", "longitudeStart", True),
            ("Lat End", "latitudeEnd", True),
            ("Lon End", "longitudeEnd", True),
        ], display),
        _card_if_has_data("Provenance", [
            ("SRA Accession", "sraAccession", True),
            ("INSDC Center", "insdcCenterName", False),
            ("INSDC Status", "insdcStatus", False),
            ("First Public", "insdcFirstPublic", False),
            ("Last Update", "insdcLastUpdate", False),
        ], display),
    ]
    cards = [c for c in core_cards if c is not None]

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

    # Append conditional new boxes after Custom Fields per spec.
    cards.extend(c for c in extra_cards if c is not None)

    # Map (full width, on top)
    if location and location.get("lat") is not None and location.get("lon") is not None:
        lat = float(location["lat"])
        lon = float(location["lon"])
        map_component = dl.Map(
            [
                dl.TileLayer(
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                ),
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
