import math
import dash
from dash import callback, Output, Input, html, dcc
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import requests

PAGE_SIZE = 10
import os
BACKEND_URL = os.getenv("BACKEND_URL", "https://portal.aegisearth.bio/api")

dash.register_page(
    __name__,
    title="Data Portal - AEGIS",
)


def _filter_card(title, checklist):
    """Create a filter card with a title and scrollable checklist."""
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    title,
                    style={
                        "fontSize": "0.8rem",
                        "fontWeight": "600",
                        "color": "var(--aegis-text-secondary)",
                        "marginBottom": "0.5rem",
                    },
                ),
                html.Div(
                    checklist,
                    style={
                        "maxHeight": "160px",
                        "overflowY": "auto",
                    },
                ),
            ],
            style={"padding": "0.75rem"},
        ),
    )


def status_legend():
    """Create the pipeline status legend component."""
    return html.Div(
        [
            html.Span("Pipeline Status:", className="text-muted me-2"),
            dbc.Badge("Submitted to Biosamples", pill=True, color="secondary"),
            html.Span("→", className="arrow mx-2"),
            dbc.Badge("Raw Data - Submitted", pill=True, color="primary"),
            html.Span("→", className="arrow mx-2"),
            dbc.Badge("Assemblies - Submitted", pill=True, color="success"),
            html.Span("→", className="arrow mx-2"),
            dbc.Badge("Annotation Completed", pill=True, color="info"),
            html.Span("→", className="arrow mx-2"),
            dbc.Badge("Annotation - Submitted", pill=True, color="danger"),
        ],
        className="status-legend",
    )


layout = dbc.Container(
    [
        # Page Header
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H1(
                            "Data Portal",
                            style={
                                "fontFamily": "var(--font-display)",
                                "fontSize": "2.5rem",
                                "marginBottom": "0.5rem",
                            },
                        ),
                        html.P(
                            "Browse genomic data contributed by the AEGIS consortium.",
                            style={"color": "var(--aegis-text-muted)"},
                        ),
                    ],
                    className="mb-4 pt-4",
                ),
            ),
        ),
        # Main Content
        dbc.Row(
            [
                # Filters Sidebar
                dbc.Col(
                    dbc.Stack(
                        [
                            _filter_card("Data Status", dbc.Checklist(id="checklist_input")),
                            _filter_card("Kingdom", dbc.Checklist(id="kingdom_filter")),
                            _filter_card("Order", dbc.Checklist(id="order_filter")),
                            _filter_card("Family", dbc.Checklist(id="family_filter")),
                            _filter_card("Country", dbc.Checklist(id="country_filter")),
                        ],
                        gap=2,
                    ),
                    id="filters-card",
                    md=3,
                    style={"marginBottom": "1rem"},
                ),
                # Main Data Area
                dbc.Col(
                    dbc.Spinner(
                        dbc.Stack(
                            [
                                # Search Input
                                html.Div(
                                    dbc.Input(
                                        id="input",
                                        placeholder="Search by species name, taxonomy, or keywords...",
                                        type="text",
                                        debounce=True,
                                        style={
                                            "background": "var(--aegis-bg-elevated)",
                                            "border": "1px solid var(--aegis-border-medium)",
                                            "color": "var(--aegis-text-primary)",
                                            "padding": "0.75rem 1rem",
                                            "fontSize": "0.95rem",
                                        },
                                    ),
                                    className="mb-3",
                                ),
                                # Map
                                html.Div(
                                    dl.Map(
                                        [
                                            dl.TileLayer(
                                                url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
                                                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                                            ),
                                            dl.LayerGroup(id="map-markers"),
                                        ],
                                        id="sample-map",
                                        center=[30, 0],
                                        zoom=2,
                                        style={
                                            "height": "400px",
                                            "borderRadius": "var(--radius-md)",
                                            "border": "1px solid var(--aegis-border-subtle)",
                                            "marginBottom": "1rem",
                                        },
                                    ),
                                    id="map-container",
                                ),
                                dcc.Store(id="map-bounds"),
                                dcc.Store(id="active-filters"),
                                # Status Legend
                                status_legend(),
                                # Data Table
                                html.Div(id="data_table"),
                                # Pagination
                                dbc.Pagination(
                                    id="pagination",
                                    max_value=1,
                                    first_last=True,
                                    previous_next=True,
                                    fully_expanded=False,
                                    className="justify-content-end mt-3",
                                ),
                            ],
                            gap=3,
                        ),
                        color="warning",
                        spinner_style={"width": "2rem", "height": "2rem"},
                    ),
                    md=9,
                ),
            ],
            className="mb-5",
        ),
    ],
    className="pb-5",
)


def return_tax_id_link(scientific_name: str, tax_id: str) -> html.A:
    """Create a link to the species detail page.

    Underlined so the affordance reads as clickable even within a table
    of styled scientific names (italic + teal already differentiates them
    from plain data, but doesn't on its own signal 'link').
    """
    return html.A(
        scientific_name,
        href=f"/data-portal/{tax_id}",
        style={
            "color": "var(--aegis-accent-primary)",
            "fontWeight": "500",
            "textDecoration": "underline",
            "textUnderlineOffset": "3px",
            "textDecorationThickness": "1px",
        },
    )


from .utils import return_badge_status  # noqa: E402


@callback(
    Output("data_table", "children"),
    Output("checklist_input", "options"),
    Output("pagination", "max_value"),
    Output("kingdom_filter", "options"),
    Output("order_filter", "options"),
    Output("family_filter", "options"),
    Output("country_filter", "options"),
    Output("active-filters", "data"),
    Input("checklist_input", "value"),
    Input("input", "value"),
    Input("pagination", "active_page"),
    Input("kingdom_filter", "value"),
    Input("order_filter", "value"),
    Input("family_filter", "value"),
    Input("country_filter", "value"),
    Input("map-bounds", "data"),
    running=[
        (Output("input", "class_name"), "invisible", "visible"),
        (Output("pagination", "class_name"), "invisible", "justify-content-end"),
        (Output("filters-card", "class_name"), "invisible", "card-title"),
    ],
)
def create_update_data_table(
    filter_values, input_value, active_page,
    kingdom_values, order_values, family_values, country_values, map_bounds,
):
    """Update the data table based on filters and search input."""
    # Build filters
    statuses = {
        "bioSamplesStatus": "Submitted to BioSamples",
        "rawDataStatus": "Raw Data submitted to ENA",
        "assembliesStatus": "Assemblies submitted to ENA",
    }
    params = {}
    try:
        for value in filter_values:
            params[value] = "Done"
    except TypeError:
        pass
    if input_value:
        params["q"] = input_value

    # Taxonomy / country filters
    if kingdom_values:
        params["kingdom"] = kingdom_values[0]
    if order_values:
        params["tax_order"] = order_values[0]
    if family_values:
        params["family"] = family_values[0]
    if country_values:
        params["countries"] = country_values[0]

    # Map bounds filters — only apply if map-bounds was the trigger
    # (not when search/filter inputs changed, which would make bounds stale)
    triggered = [t["prop_id"] for t in dash.callback_context.triggered]
    bounds_active = map_bounds and any("map-bounds" in t for t in triggered)
    if bounds_active:
        params["top_left_lat"] = map_bounds.get("top_left_lat")
        params["top_left_lon"] = map_bounds.get("top_left_lon")
        params["bottom_right_lat"] = map_bounds.get("bottom_right_lat")
        params["bottom_right_lon"] = map_bounds.get("bottom_right_lon")

    # Pagination params
    page = active_page or 1
    start = (page - 1) * PAGE_SIZE
    params["start"] = start
    params["size"] = PAGE_SIZE

    # Fetch
    response = requests.get(
        f"{BACKEND_URL}/data_portal",
        params=params,
        timeout=30,
    ).json()

    # Table
    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th(v)
                    for v in [
                        "Scientific Name",
                        "Common Name",
                        "Samples",
                        "Current Status",
                    ]
                ]
            )
        )
    ]

    results = response.get("results", [])

    if not results:
        empty_state = html.Div(
            [
                html.Div(
                    "🔍",
                    style={"fontSize": "3rem", "marginBottom": "1rem", "opacity": "0.5"},
                ),
                html.H4(
                    "No results found",
                    style={
                        "fontFamily": "var(--font-display)",
                        "color": "var(--aegis-text-secondary)",
                    },
                ),
                html.P(
                    "Try adjusting your search terms or filters",
                    style={"color": "var(--aegis-text-muted)"},
                ),
            ],
            className="text-center py-5",
        )
        return empty_state, [], 1, [], [], [], [], {}

    table_body = [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(return_tax_id_link(row["scientificName"], row["taxId"])),
                        html.Td(
                            row.get("commonName") or "—",
                            style={"color": "var(--aegis-text-secondary)"},
                        ),
                        html.Td(row.get("sampleCount", 0)),
                        html.Td(return_badge_status(row["currentStatus"])),
                    ]
                )
                for row in results
            ]
        )
    ]
    table = dbc.Table(
        table_header + table_body,
        striped=True,
        bordered=False,
        hover=True,
        responsive=True,
        style={"marginBottom": "0"},
    )

    # Wrap table in a styled container
    table_container = html.Div(
        table,
        style={
            "background": "var(--aegis-bg-card)",
            "borderRadius": "var(--radius-md)",
            "border": "1px solid var(--aegis-border-subtle)",
            "overflow": "hidden",
        },
    )

    # Checklist options from aggregations
    options = []
    for status_key, status_name in statuses.items():
        for bucket in (
            response.get("aggregations", {}).get(status_key, {}).get("buckets", [])
        ):
            if bucket.get("key") == "Done":
                options.append(
                    {
                        "label": f"{status_name} ({bucket.get('doc_count', 0)})",
                        "value": status_key,
                    }
                )

    # Taxonomy / country checklist options from aggregations
    aggregations = response.get("aggregations", {})
    kingdom_options = [
        {"label": f"{b['key']} ({b['doc_count']})", "value": b["key"]}
        for b in aggregations.get("kingdom", {}).get("buckets", [])
    ]
    order_options = [
        {"label": f"{b['key']} ({b['doc_count']})", "value": b["key"]}
        for b in aggregations.get("tax_order", {}).get("buckets", [])
    ]
    family_options = [
        {"label": f"{b['key']} ({b['doc_count']})", "value": b["key"]}
        for b in aggregations.get("family", {}).get("buckets", [])
    ]
    country_options = [
        {"label": f"{b['key']} ({b['doc_count']})", "value": b["key"]}
        for b in aggregations.get("countries", {}).get("buckets", [])
    ]

    # Compute total pages from backend total
    total = response.get("total")
    if isinstance(total, dict):
        total = total.get("value")
    if not isinstance(total, int):
        total = len(results)
    max_pages = max(1, math.ceil(total / PAGE_SIZE))

    # Collect all taxIds from the full filtered result for the map
    # (response.total may be > PAGE_SIZE, but we have the current page's taxIds
    # plus we pass the filter params so the map can query independently)
    active = {}
    if input_value:
        active["q"] = input_value
    if country_values:
        active["country"] = country_values[0] if isinstance(country_values, list) else country_values
    if kingdom_values:
        active["kingdom"] = kingdom_values[0] if isinstance(kingdom_values, list) else kingdom_values
    if order_values:
        active["tax_order"] = order_values[0] if isinstance(order_values, list) else order_values
    if family_values:
        active["family"] = family_values[0] if isinstance(family_values, list) else family_values
    if filter_values:
        status_to_tracking = {
            "bioSamplesStatus": "Submitted to BioSamples",
            "rawDataStatus": "Raw Data - Submitted",
            "assembliesStatus": "Assemblies - Submitted",
        }
        for fv in filter_values:
            if fv in status_to_tracking:
                active["trackingSystem"] = status_to_tracking[fv]
                break

    return (
        table_container, options, max_pages,
        kingdom_options, order_options, family_options, country_options,
        active,
    )


@callback(
    Output("map-markers", "children"),
    Input("sample-map", "viewport"),
    Input("active-filters", "data"),
)
def update_map_clusters(viewport, active_filters):
    """Fetch geo clusters filtered by active search/filters."""
    zoom = 2
    params = {"zoom": zoom}

    if viewport and viewport.get("bounds"):
        bounds = viewport["bounds"]
        zoom = viewport.get("zoom", 2)
        params = {
            "zoom": zoom,
            "top_left_lat": bounds[1][0],
            "top_left_lon": bounds[0][1],
            "bottom_right_lat": bounds[0][0],
            "bottom_right_lon": bounds[1][1],
        }

    # Pass active filters to geo_aggregation
    if active_filters:
        for key in ("q", "country", "trackingSystem"):
            if active_filters.get(key):
                params[key] = active_filters[key]

        # Taxonomy filters (kingdom, order, family) live on data_portal, not samples.
        # If any are set, fetch matching taxIds from data_portal and pass to geo_aggregation.
        has_taxonomy = any(active_filters.get(k) for k in ("kingdom", "tax_order", "family"))
        if has_taxonomy:
            dp_params = {"size": 10000, "start": 0}
            for k in ("kingdom", "tax_order", "family"):
                if active_filters.get(k):
                    dp_params[k] = active_filters[k]
            try:
                dp_resp = requests.get(f"{BACKEND_URL}/data_portal", params=dp_params, timeout=15).json()
                tax_ids = [str(r["taxId"]) for r in dp_resp.get("results", [])]
                if tax_ids:
                    params["tax_ids"] = ",".join(tax_ids)
                else:
                    return []  # No matching species, no markers
            except Exception:
                pass

    try:
        response = requests.get(
            f"{BACKEND_URL}/samples/geo_aggregation",
            params=params,
            timeout=15,
        ).json()
    except Exception:
        return []

    markers = []
    for c in response.get("clusters", []):
        markers.append(
            dl.CircleMarker(
                center=[c["lat"], c["lon"]],
                radius=max(8, min(30, c["count"] / 2)),
                children=dl.Tooltip(f"{c['count']} samples"),
                id={"type": "map-cluster", "key": c["key"]},
                color="#4E6B66",
                fillColor="#4E6B66",
                fillOpacity=0.7,
            )
        )
    return markers


@callback(
    Output("map-bounds", "data"),
    Output("sample-map", "viewport"),
    Input({"type": "map-cluster", "key": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def on_cluster_click(n_clicks):
    """When a cluster is clicked, zoom in and filter table by that area."""
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks):
        return dash.no_update, dash.no_update

    # Find which cluster was clicked
    triggered = ctx.triggered[0]
    prop_id = triggered["prop_id"]
    # Extract key like "12/2047/1362" from the pattern-match ID
    import json as _json
    try:
        id_dict = _json.loads(prop_id.split(".")[0])
        tile_key = id_dict["key"]
    except Exception:
        return dash.no_update, dash.no_update

    # Parse geotile key: zoom/x/y → compute bounding box
    parts = tile_key.split("/")
    if len(parts) != 3:
        return dash.no_update, dash.no_update

    z, x, y = int(parts[0]), int(parts[1]), int(parts[2])
    import math as _math
    n = 2 ** z

    def tile_to_lon(tx):
        return tx / n * 360.0 - 180.0

    def tile_to_lat(ty):
        lat_rad = _math.atan(_math.sinh(_math.pi * (1 - 2 * ty / n)))
        return _math.degrees(lat_rad)

    bounds_data = {
        "top_left_lat": tile_to_lat(y),
        "top_left_lon": tile_to_lon(x),
        "bottom_right_lat": tile_to_lat(y + 1),
        "bottom_right_lon": tile_to_lon(x + 1),
    }

    # Zoom the map to the cluster area
    center_lat = (bounds_data["top_left_lat"] + bounds_data["bottom_right_lat"]) / 2
    center_lon = (bounds_data["top_left_lon"] + bounds_data["bottom_right_lon"]) / 2
    new_viewport = {"center": [center_lat, center_lon], "zoom": z + 2}

    return bounds_data, new_viewport
