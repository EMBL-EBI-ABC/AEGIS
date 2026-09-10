"""
most abundant taxa shown side by side as silhouettes of DNA share against calibrated age, each
scaled to its own peak.
"""

import os

import dash
import requests
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BACKEND_URL = os.getenv("BACKEND_URL", "https://portal.aegisearth.bio/api")
ACCENT = "#4E6B66"

dash.register_page(__name__, path="/environmental-dna/stratigraphy", title="Stratigraphy - AEGIS", order=2)

_TOP_N = 12


def _fetch_top_taxa():
    try:
        r = requests.get(
            f"{BACKEND_URL}/data_portal",
            params={"dataType": "environmental_dna", "sort_field": "readTotal",
                    "sort_order": "desc", "size": _TOP_N},
            timeout=30,
        ).json()
        return r.get("results", [])
    except Exception:
        return []


def _diagram(taxa):
    taxa = [t for t in taxa if t.get("abundance")]
    if not taxa:
        return None
    n = len(taxa)
    titles = [f"{t.get('scientificName','?')}  ·  peak {max((p.get('prop',0) for p in t['abundance']), default=0):.1f}%"
              for t in taxa]
    fig = make_subplots(rows=n, cols=1, shared_xaxes=True, vertical_spacing=0.045,
                        subplot_titles=titles)
    for i, t in enumerate(taxa, start=1):
        ab = sorted(t["abundance"], key=lambda p: p.get("age", 0))
        xs = [p.get("age") for p in ab]
        ys = [p.get("prop", 0) for p in ab]
        peak = max(ys) if ys else 1
        fig.add_trace(
            go.Scatter(
                x=xs, y=ys, mode="lines", fill="tozeroy",
                line={"color": ACCENT, "width": 1.5},
                fillcolor="rgba(78,107,102,0.22)",
                name=t.get("scientificName", ""),
                hovertemplate="≈%{x} CE<br>%{y:.2f}%<extra>" + t.get("scientificName", "") + "</extra>",
            ),
            row=i, col=1,
        )
        fig.update_yaxes(range=[0, peak * 1.3], showticklabels=False,
                         showgrid=False, zeroline=False, row=i, col=1)
        fig.update_xaxes(showgrid=False, zeroline=False, row=i, col=1)
    fig.update_xaxes(title_text="Year (CE) — older ← → recent", row=n, col=1)
    fig.update_layout(
        height=max(420, 94 * n), showlegend=False,
        margin={"l": 20, "r": 20, "t": 26, "b": 45},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#6b7772", "size": 11},
        hoverlabel={"bgcolor": "#19211d", "font": {"color": "#f0f3ef"}},
    )
    for ann in fig.layout.annotations:  # subplot titles: left-align, italic, smaller
        ann.update(x=0.004, xanchor="left", yanchor="bottom",
                   font={"size": 12, "color": "#2b3733"},
                   bgcolor="rgba(255,255,255,0.8)", borderpad=3)
    return fig


def _await_panel(title, detail, needs):
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Span(title, style={"fontWeight": "600", "color": "var(--aegis-text-primary)"}),
                dbc.Badge("Awaiting data", color="warning", pill=True, className="ms-2"),
            ], style={"marginBottom": "0.5rem"}),
            html.P(detail, style={"color": "var(--aegis-text-secondary)", "fontSize": "0.9rem", "marginBottom": "0.5rem"}),
            html.P(needs, style={"color": "var(--aegis-text-muted)", "fontSize": "0.8rem", "marginBottom": "0",
                                 "fontStyle": "italic"}),
        ]),
        style={"background": "var(--aegis-bg-elevated)", "border": "1px dashed var(--aegis-border-subtle)",
               "height": "100%"},
    )


def layout(**kwargs):
    taxa = _fetch_top_taxa()
    fig = _diagram(taxa)

    if fig is not None:
        diagram = dcc.Graph(figure=fig, config={"displayModeBar": False})
        note = html.P(
            "Each strip is one taxon; left is older, right more recent; height is that taxon's "
            "share of DNA in each dated layer, scaled to its own peak (shown in the label) so the "
            "timing of change compares across taxa even when the amounts don't. Read share is a "
            "relative-abundance proxy, not a direct count.",
            style={"color": "var(--aegis-text-muted)", "fontSize": "0.82rem", "maxWidth": "60em"},
        )
    else:
        diagram = dbc.Alert(
            "No environmental-DNA taxa found. Make sure the local backend points at the "
            "aegis_test_* indices and the importer has run.",
            color="secondary",
        )
        note = html.Div()

    return dbc.Container([
        dbc.Row(dbc.Col(html.Div([
            html.A(["← ", "Back to Environmental DNA"], href="/environmental-dna",
                   style={"color": "var(--aegis-text-muted)", "textDecoration": "underline",
                          "textUnderlineOffset": "3px", "fontSize": "0.9rem"}),
            html.H1("Tjörnin core — stratigraphic view", style={"marginTop": "0.75rem", "marginBottom": "0.4rem"}),
            html.P(
                f"The {len(taxa)} most abundant taxa through the Iceland lake-sediment core, oldest at left.",
                style={"color": "var(--aegis-text-secondary)", "maxWidth": "48em"},
            ),
        ], className="pt-4 pb-2"))),
        dbc.Row(dbc.Col(dbc.Card(dbc.CardBody([diagram, note]),
                                 style={"background": "var(--aegis-bg-card)",
                                        "border": "1px solid var(--aegis-border-subtle)"}),
                        md={"width": 10, "offset": 1})),
        # Data-quality panels awaiting Carl's data.
        dbc.Row(dbc.Col(html.H4("Data quality", style={"marginTop": "2rem", "marginBottom": "0.75rem"}),
                        md={"width": 10, "offset": 1})),
        dbc.Row(dbc.Col(dbc.Row([
            dbc.Col(_await_panel(
                "Ancient-DNA authenticity",
                "Whether each taxon's DNA shows the tell-tale damage of genuine ancient DNA "
                "(C→T at fragment ends) rather than modern contamination.",
                "Needs the DNA-damage statistics Carl offered in August — not in the current files.",
            ), md=6, className="mb-3"),
            dbc.Col(_await_panel(
                "Contamination flags",
                "Taxa also detected in the blank/negative controls, flagged as likely lab or "
                "reagent contamination rather than real lake signal.",
                "Needs the taxonomy of the 15 blank controls — the current file covers only the 62 sediment layers.",
            ), md=6, className="mb-3"),
        ]), md={"width": 10, "offset": 1})),
    ], className="pb-5")
