"""
A heatmap of every detected genus (rows) against the dated core
layers (columns), coloured by each genus's share of DNA in that layer, with
filters to narrow the question and click-through to detail.

Filters
  - Taxonomic group   (phylogeny.kingdom)
  - Age window
  - Minimum peak share (drop taxa that never rise above a threshold — noise)
  - Number of taxa    (top-N by total reads, to keep the grid legible)
  - Row order + colour scaling (linear shows dominance; log reveals rare taxa)
"""

import os

import dash
import requests
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

BACKEND_URL = os.getenv("BACKEND_URL", "http://0.0.0.0:8080/api")
ACCENT = "#4E6B66"

GREEN_SCALE = [
    [0.0, "#f3f6f4"], [0.15, "#d5e2dc"], [0.35, "#a9c4ba"],
    [0.55, "#7aa398"], [0.75, "#517d72"], [1.0, "#243c35"],
]

dash.register_page(__name__, path="/environmental-dna",
                   title="Environmental DNA - AEGIS", order=1)


# --------------------------------------------------------------------------
# Data access
# --------------------------------------------------------------------------
def _fetch_edna():
    try:
        r = requests.get(
            f"{BACKEND_URL}/data_portal",
            params={"dataType": "environmental_dna", "sort_field": "readTotal",
                    "sort_order": "desc", "size": 500},
            timeout=30,
        ).json()
        return r.get("results", [])
    except Exception:
        return []


def _clean(taxa):
    #Keep only taxa with a usable abundance series
    out = []
    for t in taxa:
        ab = [p for p in (t.get("abundance") or []) if p.get("age") is not None]
        if not ab:
            continue
        out.append({
            "taxId": t.get("taxId"),
            "name": t.get("scientificName") or str(t.get("taxId")),
            "kingdom": (t.get("phylogeny") or {}).get("kingdom") or "Unassigned",
            "readTotal": t.get("readTotal") or 0,
            "abundance": {int(p["age"]): float(p.get("prop", 0) or 0) for p in ab},
        })
    return out


# --------------------------------------------------------------------------
# Controls
# --------------------------------------------------------------------------
def _controls(taxa):
    kingdoms = sorted({t["kingdom"] for t in taxa})
    ages = sorted({a for t in taxa for a in t["abundance"]})
    amin, amax = (ages[0], ages[-1]) if ages else (0, 2000)
    step = 100
    marks = {int(a): {"label": str(int(a)),
                      "style": {"color": "var(--aegis-text-muted)", "fontSize": "0.7rem"}}
             for a in range(int(amin // step * step), int(amax) + step, step * 3)}

    label = {"fontWeight": "600", "fontSize": "0.8rem",
             "color": "var(--aegis-text-primary)", "marginBottom": "0.3rem",
             "display": "block", "marginTop": "1rem"}

    return dbc.Card(dbc.CardBody([
        html.Div("Filters", style={"fontWeight": "700", "fontSize": "0.95rem",
                                    "color": "var(--aegis-text-primary)"}),

        html.Label("Taxonomic group", style=label),
        dcc.Checklist(
            id="edna-kingdom",
            options=[{"label": " " + k, "value": k} for k in kingdoms],
            value=kingdoms, labelStyle={"display": "block", "fontSize": "0.82rem"},
            inputStyle={"marginRight": "0.35rem"},
        ),

        html.Label("Age window (year CE)", style=label),
        dcc.RangeSlider(id="edna-age", min=int(amin), max=int(amax),
                        value=[int(amin), int(amax)], step=10, marks=marks,
                        tooltip={"placement": "bottom", "always_visible": False}),

        html.Label("Minimum peak share (%)", style=label),
        dcc.Slider(id="edna-thresh", min=0, max=10, step=0.5, value=0,
                   marks={0: "0", 5: "5", 10: "10"},
                   tooltip={"placement": "bottom", "always_visible": False}),

        html.Label("Number of taxa shown", style=label),
        dcc.Slider(id="edna-topn", min=10, max=120, step=10, value=40,
                   marks={10: "10", 60: "60", 120: "120"},
                   tooltip={"placement": "bottom", "always_visible": False}),

        html.Label("Order rows by", style=label),
        dcc.Dropdown(id="edna-sort", clearable=False, value="readTotal",
                     options=[{"label": "Total abundance", "value": "readTotal"},
                              {"label": "First appearance (oldest)", "value": "first"},
                              {"label": "Time of peak", "value": "peak"},
                              {"label": "Name (A–Z)", "value": "name"}],
                     style={"fontSize": "0.82rem"}),

        html.Label("Colour scaling", style=label),
        dcc.RadioItems(id="edna-scale", value="log",
                       options=[{"label": " Log (reveals rare taxa)", "value": "log"},
                                {"label": " Linear (shows dominance)", "value": "linear"}],
                       labelStyle={"display": "block", "fontSize": "0.82rem"},
                       inputStyle={"marginRight": "0.35rem"}),
    ]), style={"background": "var(--aegis-bg-card)",
               "border": "1px solid var(--aegis-border-subtle)", "position": "sticky",
               "top": "1rem"})


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------
def _filter_sort(taxa, kingdoms, age_range, thresh, topn, sort):
    lo, hi = age_range
    rows = []
    for t in taxa:
        if t["kingdom"] not in kingdoms:
            continue
        series = {int(a): p for a, p in t["abundance"].items() if lo <= int(a) <= hi}
        if not series:
            continue
        peak = max(series.values())
        if peak < thresh:
            continue
        rows.append({**t, "series": series, "peak": peak,
                     "first": min(series), "peak_age": max(series, key=series.get)})
    if sort == "name":
        rows.sort(key=lambda r: r["name"].lower())
    elif sort == "first":
        rows.sort(key=lambda r: r["first"])
    elif sort == "peak":
        rows.sort(key=lambda r: r["peak_age"])
    else:
        rows.sort(key=lambda r: r["readTotal"], reverse=True)
    keep = set(sorted(range(len(rows)), key=lambda i: rows[i]["readTotal"],
                      reverse=True)[:topn])
    return [r for i, r in enumerate(rows) if i in keep]


def _heatmap(rows, scale):
    if not rows:
        return None
    ages = sorted({a for r in rows for a in r["series"]})
    names = [r["name"] for r in rows]
    z, custom = [], []
    for r in rows:
        zr, cr = [], []
        for a in ages:
            p = r["series"].get(a)
            cr.append(p if p is not None else float("nan"))
            if p is None or p <= 0:
                zr.append(None)
            else:
                import math
                zr.append(math.log10(p) if scale == "log" else p)
        z.append(zr)
        custom.append(cr)

    if scale == "log":
        cbar = dict(title="share", tickvals=[-2, -1, 0, 1, 2],
                    ticktext=["0.01%", "0.1%", "1%", "10%", "100%"],
                    thickness=12, len=0.6)
    else:
        cbar = dict(title="share (%)", thickness=12, len=0.6)

    fig = go.Figure(go.Heatmap(
        z=z, x=[str(a) for a in ages], y=names, customdata=custom,
        colorscale=GREEN_SCALE, colorbar=cbar,
        hoverongaps=False, xgap=0.5, ygap=0.5,
        hovertemplate="<b>%{y}</b><br>≈%{x} CE<br>%{customdata:.2f}% of layer DNA<extra></extra>",
    ))
    tick_every = max(1, len(ages) // 12)
    fig.update_xaxes(title_text="Dated core layers — older ← → recent  (year CE)",
                     tickvals=[str(a) for i, a in enumerate(ages) if i % tick_every == 0],
                     tickangle=-45, showgrid=False)
    fig.update_yaxes(autorange="reversed", tickfont={"size": 10}, showgrid=False)
    fig.update_layout(
        height=max(420, 20 * len(names) + 120),
        margin={"l": 10, "r": 10, "t": 10, "b": 70},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#6b7772", "size": 11},
        hoverlabel={"bgcolor": "#19211d", "font": {"color": "#f0f3ef"}},
    )
    return fig


def _genus_curve(row):
    ages = sorted(row["series"])
    ys = [row["series"][a] for a in ages]
    fig = go.Figure(go.Scatter(
        x=ages, y=ys, mode="lines+markers", fill="tozeroy",
        line={"color": ACCENT, "width": 2}, marker={"size": 5, "color": ACCENT},
        fillcolor="rgba(78,107,102,0.18)",
        hovertemplate="≈%{x} CE<br>%{y:.2f}%<extra></extra>",
    ))
    fig.update_xaxes(title_text="Year (CE)", showgrid=False)
    fig.update_yaxes(title_text="share of layer DNA (%)", showgrid=True,
                     gridcolor="rgba(0,0,0,0.06)")
    fig.update_layout(height=280, margin={"l": 55, "r": 15, "t": 40, "b": 40},
                      title={"text": row["name"], "font": {"size": 14, "color": "#3c4a44"}},
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font={"color": "#6b7772", "size": 11})
    return fig


def _layer_community(rows, age):
    items = []
    for r in rows:
        p = r["series"].get(age)
        if p:
            items.append((r["name"], p))
    items.sort(key=lambda x: x[1], reverse=True)
    items = items[:15][::-1]
    fig = go.Figure(go.Bar(
        x=[p for _, p in items], y=[n for n, _ in items], orientation="h",
        marker={"color": ACCENT},
        hovertemplate="%{y}<br>%{x:.2f}%<extra></extra>",
    ))
    fig.update_xaxes(title_text="share of layer DNA (%)", showgrid=True,
                     gridcolor="rgba(0,0,0,0.06)")
    fig.update_yaxes(tickfont={"size": 10}, showgrid=False)
    fig.update_layout(height=280, margin={"l": 10, "r": 15, "t": 40, "b": 40},
                      title={"text": f"Community at ≈{age} CE (top taxa shown)",
                             "font": {"size": 14, "color": "#3c4a44"}},
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font={"color": "#6b7772", "size": 11})
    return fig


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------
def layout(**kwargs):
    taxa = _clean(_fetch_edna())

    if not taxa:
        return dbc.Container(dbc.Alert(
            "No environmental-DNA taxa found. Start the local backend pointed at the "
            "aegis_test_* indices (and the front-end with BACKEND_URL set), then reload.",
            color="secondary"), className="py-5")

    n_layers = len({a for t in taxa for a in t["abundance"]})

    header = html.Div([
        html.A(["← ", "Back to Data Portal"], href="/data-portal",
               style={"color": "var(--aegis-text-muted)", "textDecoration": "underline",
                      "textUnderlineOffset": "3px", "fontSize": "0.9rem"}),
        html.H1("Environmental DNA — community explorer",
                style={"marginTop": "0.75rem", "marginBottom": "0.4rem"}),
        html.P([
            f"Every genus of ancient DNA detected in the Tjörnin lake core "
            f"({len(taxa)} taxa across {n_layers} dated layers), ~1,800 years of change. "
            "Filter to your question; click any cell to pin the genus through time and "
            "the whole community of that layer. ",
            html.A("See the stratigraphic poster view →", href="/environmental-dna/stratigraphy",
                   style={"color": ACCENT, "textDecoration": "underline",
                          "textUnderlineOffset": "3px"}),
        ], style={"color": "var(--aegis-text-secondary)", "maxWidth": "60em"}),
        html.P(
            "Colour is each genus's share of DNA reads in a layer — a relative-abundance "
            "proxy, not a count. Layer ages are median calibrated years CE, provisional "
            "pending confirmation.",
            style={"color": "var(--aegis-text-muted)", "fontSize": "0.8rem",
                   "fontStyle": "italic", "maxWidth": "60em"}),
    ], className="pt-4 pb-2")

    grid = dbc.Card(dbc.CardBody([
        dcc.Graph(id="edna-heatmap", config={"displayModeBar": False}),
    ]), style={"background": "var(--aegis-bg-card)",
               "border": "1px solid var(--aegis-border-subtle)"})

    detail = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="edna-curve", config={"displayModeBar": False})),
                         style={"background": "var(--aegis-bg-card)",
                                "border": "1px solid var(--aegis-border-subtle)",
                                "height": "100%"}), md=6, className="mb-3"),
        dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="edna-layer", config={"displayModeBar": False})),
                         style={"background": "var(--aegis-bg-card)",
                                "border": "1px solid var(--aegis-border-subtle)",
                                "height": "100%"}), md=6, className="mb-3"),
    ], className="mt-3")

    hint = html.P("Tip: click a cell in the heatmap to explore one genus and one layer.",
                  style={"color": "var(--aegis-text-muted)", "fontSize": "0.82rem",
                         "textAlign": "center", "marginTop": "0.5rem"})

    return dbc.Container([
        dcc.Store(id="edna-store", data=taxa),
        dbc.Row(dbc.Col(header)),
        dbc.Row([
            dbc.Col(_controls(taxa), md=3),
            dbc.Col([grid, hint, detail], md=9),
        ]),
    ], fluid=True, className="pb-5")


# --------------------------------------------------------------------------
# Callbacks
# --------------------------------------------------------------------------
@callback(
    Output("edna-heatmap", "figure"),
    Input("edna-kingdom", "value"),
    Input("edna-age", "value"),
    Input("edna-thresh", "value"),
    Input("edna-topn", "value"),
    Input("edna-sort", "value"),
    Input("edna-scale", "value"),
    State("edna-store", "data"),
)
def _update_heatmap(kingdoms, age_range, thresh, topn, sort, scale, taxa):
    rows = _filter_sort(taxa or [], kingdoms or [], age_range, thresh, topn, sort)
    fig = _heatmap(rows, scale)
    if fig is None:
        fig = go.Figure()
        fig.update_layout(
            height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            annotations=[{"text": "No taxa match these filters — widen the age window "
                                  "or lower the threshold.", "showarrow": False,
                          "font": {"color": "#6b7772"}}],
            xaxis={"visible": False}, yaxis={"visible": False})
    return fig


@callback(
    Output("edna-curve", "figure"),
    Output("edna-layer", "figure"),
    Input("edna-heatmap", "clickData"),
    State("edna-kingdom", "value"),
    State("edna-age", "value"),
    State("edna-thresh", "value"),
    State("edna-topn", "value"),
    State("edna-sort", "value"),
    State("edna-store", "data"),
)
def _update_detail(click, kingdoms, age_range, thresh, topn, sort, taxa):
    def _placeholder(msg):
        f = go.Figure()
        f.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        annotations=[{"text": msg, "showarrow": False,
                                      "font": {"color": "#9aa6a1"}}],
                        xaxis={"visible": False}, yaxis={"visible": False})
        return f

    if not click:
        return (_placeholder("Click a cell to see this genus through time"),
                _placeholder("Click a cell to see this layer's community"))

    rows = _filter_sort(taxa or [], kingdoms or [], age_range, thresh, topn, sort)
    pt = click["points"][0]
    name, age = pt.get("y"), int(pt.get("x"))
    row = next((r for r in rows if r["name"] == name), None)
    curve = _genus_curve(row) if row else _placeholder("Genus not in current view")
    return curve, _layer_community(rows, age)
