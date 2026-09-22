import os

import dash
import requests
from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import plotly.graph_objects as go

from .utils import basemap_props

BACKEND_URL = os.getenv("BACKEND_URL", "https://portal.aegisearth.bio/api")
ACCENT = "#4E6B66"

dash.register_page(__name__,
                   path_template="/environmental-dna/samples/<accession>",
                   title="Biosample - AEGIS", order=4)

_METADATA = [
    ("Layer / core", [
        ("Submitter id", "submitterId"),
        ("Core", "masterCoreSampleId"),
        ("Core depth", "depth"),
        ("Elevation", "elevation"),
        ("Median age (CE)", "age"),
        ("Taxa detected", "taxaCount"),
        ("Layer reads", "readTotal"),
        ("Description", "description"),
    ]),
    ("Environmental context", [
        ("Medium", "environmentalMedium"),
        ("Broad-scale", "broadScaleEnvironmentalContext"),
        ("Local", "localEnvironmentalContext"),
        ("Past broad-scale", "pastBroadScaleEnvironmentalContext"),
        ("Past local", "pastLocalEnvironmentalContext"),
    ]),
    ("Age & authenticity", [
        ("Geological epoch", "geologicalEpoch"),
        ("Age inference", "sampleAgeInferenceMethod"),
        ("Age range oldest (ka BP)", "sampleAgeRangeOldestLimit"),
        ("Age range youngest (ka BP)", "sampleAgeRangeYoungestLimit"),
        ("Damage treatment", "damageTreatment"),
    ]),
    ("Collection & provenance", [
        ("Collected by", "collectedBy"),
        ("Collection date", "collectionDate"),
        ("Institution", "collectingInstitution"),
        ("Sample coordinator", "sampleCoordinator"),
        ("SRA accession", "sraAccession"),
        ("INSDC centre", "insdcCenterName"),
        ("INSDC status", "insdcStatus"),
    ]),
]


def _fmt(key, value):
    if key == "depth":
        return f"{value:g} (core units)"
    if key == "elevation":
        return f"{value:g} m"
    if key == "age":
        return f"{value} CE"
    if key == "collectionDate":
        return str(value)[:10]
    return str(value)


def _metadata_card(title, fields, sample):
    items = []
    for label, key in fields:
        value = sample.get(key)
        if value is None or value == "" or value == []:
            continue
        items.append(html.Div([
            html.Span(label, style={
                "fontSize": "0.72rem", "color": "var(--aegis-text-muted)",
                "textTransform": "uppercase", "letterSpacing": "0.05em",
                "display": "block", "marginBottom": "0.2rem"}),
            html.Span(_fmt(key, value), style={
                "color": "var(--aegis-text-primary)", "fontSize": "0.9rem"}),
        ], style={"padding": "0.7rem", "background": "var(--aegis-bg-elevated)",
                  "borderRadius": "var(--radius-md)"}))
    if not items:
        return None
    return dbc.Card(dbc.CardBody([
        html.H6(title, style={
            "fontFamily": "var(--font-display)", "color": "var(--aegis-text-primary)",
            "marginBottom": "1rem", "fontSize": "0.85rem",
            "textTransform": "uppercase", "letterSpacing": "0.05em"}),
        html.Div(items, style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(150px, 1fr))",
            "gap": "0.6rem"}),
    ]), style={"background": "var(--aegis-bg-card)",
               "border": "1px solid var(--aegis-border-subtle)",
               "marginBottom": "1rem"})


def _community_chart(community):
    top = community[:15][::-1]
    fig = go.Figure(go.Bar(
        x=[c["prop"] for c in top], y=[c["name"] for c in top], orientation="h",
        marker={"color": ACCENT},
        hovertemplate="%{y}<br>%{x:.2f}% of layer DNA (incl. unassigned)<extra></extra>",
    ))
    fig.update_xaxes(title_text="share of layer DNA (%)", showgrid=True,
                     gridcolor="rgba(0,0,0,0.06)")
    fig.update_yaxes(tickfont={"size": 10}, showgrid=False)
    fig.update_layout(height=max(300, 22 * len(top) + 80),
                      margin={"l": 10, "r": 15, "t": 10, "b": 40},
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font={"color": "#6b7772", "size": 11})
    return fig


def _community_table(community):
    rows = []
    for c in community:
        name = c["name"]
        tid = c.get("taxId")
        name_cell = (html.A(name, href=f"/data-portal/{tid}", style={
            "color": "var(--aegis-accent-primary)", "textDecoration": "none",
            "fontStyle": "italic"}) if tid is not None
            else html.Span(name, style={"fontStyle": "italic"}))
        rows.append(html.Tr([
            html.Td(name_cell),
            html.Td(f"{c['prop']:.3f}%", style={"fontFamily": "var(--font-mono)",
                                                "fontSize": "0.82rem"}),
            html.Td(f"{c['reads']:,}", style={"fontFamily": "var(--font-mono)",
                                              "fontSize": "0.82rem",
                                              "color": "var(--aegis-text-muted)"}),
        ]))
    return dbc.Table(
        [html.Thead(html.Tr([html.Th("Genus"), html.Th("Share"),
                             html.Th("Reads")])), html.Tbody(rows)],
        striped=True, hover=True, responsive=True, borderless=True,
        style={"marginBottom": "0"})


def _not_found(accession):
    return dbc.Container(html.Div([
        html.H4("Biosample not found",
                style={"fontFamily": "var(--font-display)",
                       "color": "var(--aegis-text-secondary)"}),
        html.P(f"Could not load {accession}.",
               style={"color": "var(--aegis-text-muted)"}),
        html.A("← Back to biosamples", href="/environmental-dna/samples",
               style={"color": ACCENT}),
    ], className="text-center py-5"), className="pb-5")


def layout(accession=None, **kwargs):
    if not accession:
        return _not_found("")
    try:
        data = requests.get(f"{BACKEND_URL}/samples/{accession}", timeout=30).json()
        sample = (data.get("results") or [None])[0]
    except Exception:
        sample = None
    if not sample:
        return _not_found(accession)

    community = sample.get("community") or []
    location = sample.get("location")

    # Breadcrumb + header
    crumb = html.Div([
        html.A("Environmental DNA", href="/environmental-dna",
               style={"color": "var(--aegis-accent-primary)", "textDecoration": "none",
                      "fontSize": "0.85rem"}),
        html.Span(" → ", style={"color": "var(--aegis-text-muted)", "margin": "0 0.4rem"}),
        html.A("Biosamples", href="/environmental-dna/samples",
               style={"color": "var(--aegis-accent-primary)", "textDecoration": "none",
                      "fontSize": "0.85rem"}),
        html.Span(" → ", style={"color": "var(--aegis-text-muted)", "margin": "0 0.4rem"}),
        html.Span(accession, style={"color": "var(--aegis-text-muted)",
                                    "fontFamily": "var(--font-mono)", "fontSize": "0.85rem"}),
    ], className="pt-4 pb-2")

    link_style = {"color": "var(--aegis-accent-primary)", "textDecoration": "none",
                  "padding": "0.3rem 0.75rem", "background": "var(--aegis-bg-elevated)",
                  "borderRadius": "var(--radius-md)", "border": "1px solid var(--aegis-border-subtle)",
                  "fontSize": "0.8rem"}
    header = html.Div([
        html.H2(accession, style={"fontFamily": "var(--font-mono)",
                                  "color": "var(--aegis-accent-primary)",
                                  "marginBottom": "0.25rem"}),
        html.Div(sample.get("scientificName", "sediment metagenome"), style={
            "fontStyle": "italic", "color": "var(--aegis-text-secondary)",
            "marginBottom": "0.6rem"}),
        html.Div([
            html.A(["BioSamples ↗"],
                   href=f"https://www.ebi.ac.uk/biosamples/samples/{accession}",
                   target="_blank", rel="noopener noreferrer", style=link_style),
            html.A(["ENA ↗"],
                   href=f"https://www.ebi.ac.uk/ena/browser/view/{accession}",
                   target="_blank", rel="noopener noreferrer", style=link_style),
        ], style={"display": "flex", "gap": "0.5rem", "flexWrap": "wrap"}),
    ], style={"marginBottom": "1.25rem"})

    cards = [c for c in (_metadata_card(t, f, sample) for t, f in _METADATA) if c]

    # Community section
    if community:
        n = sample.get("taxaCount", len(community))
        community_section = dbc.Card(dbc.CardBody([
            html.H6(f"Community in this layer — {n} genera detected", style={
                "fontFamily": "var(--font-display)", "color": "var(--aegis-text-primary)",
                "marginBottom": "0.25rem", "fontSize": "0.85rem",
                "textTransform": "uppercase", "letterSpacing": "0.05em"}),
            html.P("Each genus's share of the layer's DNA (a relative-abundance proxy, "
                   "incl. unassigned reads in the denominator). Names link to the genus "
                   "through time.", style={"color": "var(--aegis-text-muted)",
                                           "fontSize": "0.8rem", "fontStyle": "italic"}),
            dbc.Row([
                dbc.Col(dcc.Graph(figure=_community_chart(community),
                                  config={"displayModeBar": False}), md=6),
                dbc.Col(html.Div(_community_table(community),
                                 style={"maxHeight": "460px", "overflowY": "auto"}), md=6),
            ]),
        ]), style={"background": "var(--aegis-bg-card)",
                   "border": "1px solid var(--aegis-border-subtle)",
                   "marginBottom": "1rem"})
    else:
        community_section = dbc.Alert(
            "No community linked to this layer yet. Run the layer-community "
            "enrichment (importer.enrich_layer_communities) or re-import.",
            color="secondary")

    # Map
    map_card = None
    if location and location.get("lat") is not None:
        map_card = dbc.Card(dbc.CardBody(dl.Map([
            dl.TileLayer(**basemap_props()),
            dl.Marker(position=[location["lat"], location["lon"]]),
        ], center=[location["lat"], location["lon"]], zoom=11,
            style={"height": "260px", "borderRadius": "var(--radius-md)"}),
            style={"padding": "0"}),
            style={"background": "var(--aegis-bg-card)", "overflow": "hidden",
                   "border": "1px solid var(--aegis-border-subtle)", "marginBottom": "1rem"})

    left = cards[::2]
    right = cards[1::2]
    return dbc.Container([
        crumb, header,
        community_section,
        dbc.Row([dbc.Col(left, md=6), dbc.Col(right, md=6)]),
        map_card or html.Div(),
        html.A("← Back to all biosamples", href="/environmental-dna/samples",
               style={"color": ACCENT, "textDecoration": "underline",
                      "textUnderlineOffset": "3px"}),
    ], className="pb-5")
