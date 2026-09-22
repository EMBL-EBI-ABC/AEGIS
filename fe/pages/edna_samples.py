import os

import dash
import requests
from dash import html, dcc
import dash_bootstrap_components as dbc

BACKEND_URL = os.getenv("BACKEND_URL", "https://portal.aegisearth.bio/api")
ACCENT = "#4E6B66"

dash.register_page(__name__, path="/environmental-dna/samples",
                   title="Iceland Biosamples - AEGIS", order=3)

_CONTEXT_FIELDS = [
    ("Site", "locality"),
    ("Country", "country"),
    ("Core", "masterCoreSampleId"),
    ("Environmental medium", "environmentalMedium"),
    ("Broad-scale context", "broadScaleEnvironmentalContext"),
    ("Local context", "localEnvironmentalContext"),
    ("Past broad-scale context", "pastBroadScaleEnvironmentalContext"),
    ("Past local context", "pastLocalEnvironmentalContext"),
    ("Geological epoch", "geologicalEpoch"),
    ("Age inference", "sampleAgeInferenceMethod"),
]


def _fetch_samples():
    try:
        r = requests.get(
            f"{BACKEND_URL}/samples",
            params={"dataType": "environmental_dna", "size": 100},
            timeout=30,
        ).json()
        return r.get("results", [])
    except Exception:
        return []


def _muted(text, size="0.8rem", italic=False):
    style = {"color": "var(--aegis-text-muted)", "fontSize": size}
    if italic:
        style["fontStyle"] = "italic"
    return html.Span(text, style=style)


def _context_caption(sample):
    chips = []
    for label, key in _CONTEXT_FIELDS:
        val = sample.get(key)
        if not val:
            continue
        chips.append(html.Div([
            html.Span(label.upper(), style={
                "fontSize": "0.65rem", "letterSpacing": "0.05em",
                "color": "var(--aegis-text-muted)", "display": "block",
                "marginBottom": "0.1rem"}),
            html.Span(str(val), style={
                "fontSize": "0.82rem", "color": "var(--aegis-text-primary)"}),
        ], style={"padding": "0.5rem 0.75rem",
                  "background": "var(--aegis-bg-elevated)",
                  "borderRadius": "var(--radius-md)"}))
    return dbc.Card(dbc.CardBody([
        html.Div("Site provenance — shared by every layer in this core", style={
            "fontWeight": "700", "fontSize": "0.9rem",
            "color": "var(--aegis-text-primary)", "marginBottom": "0.15rem"}),
        _muted("These MIxS environmental-context values (ENVO ontology terms) are "
               "identical down the whole core: Tjörnin has been one freshwater "
               "lake throughout the record, so 'past' equals 'present'. They ground "
               "the graphs in cited metadata rather than varying layer to layer.",
               italic=True),
        html.Div(chips, style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
            "gap": "0.5rem", "marginTop": "0.75rem"}),
    ]), style={"background": "var(--aegis-bg-card)",
               "border": "1px solid var(--aegis-border-subtle)",
               "marginBottom": "1.25rem"})


def _table(samples):
    # Oldest layer first, so the table reads down-core / back in time.
    def age_key(s):
        a = s.get("age")
        return a if a is not None else 10**9
    rows_sorted = sorted(samples, key=age_key)

    header = html.Thead(html.Tr([
        html.Th("Layer (submitter id)"),
        html.Th("BioSample"),
        html.Th("Median age", title="Median calibrated age, year CE (provisional)"),
        html.Th("Core depth", title="Depth in the core (core units; provisional)"),
        html.Th("Taxa detected", title="Number of genera detected in this layer"),
        html.Th(""),
    ]))

    body_rows = []
    for s in rows_sorted:
        acc = s.get("accession", "")
        sid = s.get("submitterId", "—")
        age = s.get("age")
        depth = s.get("depth")
        taxa = s.get("taxaCount")
        detail_href = f"/environmental-dna/samples/{acc}"
        body_rows.append(html.Tr([
            html.Td(html.Span(sid, style={"fontFamily": "var(--font-mono)",
                                          "fontSize": "0.85rem"})),
            html.Td(html.A(acc, href=detail_href, style={
                "color": "var(--aegis-accent-primary)", "textDecoration": "none",
                "fontFamily": "var(--font-mono)", "fontSize": "0.85rem"})),
            html.Td(f"{age} CE" if age is not None else _muted("—")),
            html.Td(f"{depth:g}" if isinstance(depth, (int, float)) else _muted("—")),
            html.Td(str(taxa) if taxa is not None else _muted("—")),
            html.Td(html.A("View community →", href=detail_href, style={
                "color": ACCENT, "textDecoration": "underline",
                "textUnderlineOffset": "3px", "fontSize": "0.8rem"})),
        ]))

    return dbc.Card(dbc.CardBody(
        dbc.Table([header, html.Tbody(body_rows)],
                  striped=True, hover=True, responsive=True, borderless=True,
                  style={"marginBottom": "0"}),
    ), style={"background": "var(--aegis-bg-card)",
              "border": "1px solid var(--aegis-border-subtle)"})


def layout():
    samples = _fetch_samples()

    if not samples:
        return dbc.Container(dbc.Alert(
            "No environmental-DNA biosamples found. Start the local backend "
            "pointed at the aegis_test_* indices (with the ancient fields in the "
            "samples model) and the front-end with BACKEND_URL set, then reload.",
            color="secondary"), className="py-5")

    linked = sum(1 for s in samples if s.get("community"))

    header = html.Div([
        html.A(["← ", "Back to Environmental DNA"], href="/environmental-dna",
               style={"color": "var(--aegis-text-muted)", "textDecoration": "underline",
                      "textUnderlineOffset": "3px", "fontSize": "0.9rem"}),
        html.H1("Iceland biosamples — the dated core layers",
                style={"marginTop": "0.75rem", "marginBottom": "0.4rem"}),
        html.P([
            f"The {len(samples)} sediment layers of the Tjörnin lake core "
            "(negative/blank controls excluded), each a BioSample carrying its "
            "own metadata. Every genus in the portal was detected in one of these "
            "layers — click a layer to see its full record and the community found "
            "in it. ",
            html.A("Community explorer →", href="/environmental-dna",
                   style={"color": ACCENT, "textDecoration": "underline",
                          "textUnderlineOffset": "3px"}),
            html.Span("  ·  ", style={"color": "var(--aegis-text-muted)"}),
            html.A("Stratigraphy →", href="/environmental-dna/stratigraphy",
                   style={"color": ACCENT, "textDecoration": "underline",
                          "textUnderlineOffset": "3px"}),
        ], style={"color": "var(--aegis-text-secondary)", "maxWidth": "62em"}),
        _muted(f"{linked} of {len(samples)} layers linked to their taxon community. "
               "Ages are median calibrated years CE (provisional, pending Carl); "
               "core depth is in the core's own units (provisional).", italic=True),
    ], className="pt-4 pb-3")

    return dbc.Container([
        dbc.Row(dbc.Col(header)),
        dbc.Row(dbc.Col(_context_caption(samples[0]))),
        dbc.Row(dbc.Col(_table(samples))),
    ], fluid=True, className="pb-5")
