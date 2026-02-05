import math
import dash
from dash import callback, Output, Input, html
import dash_bootstrap_components as dbc
import requests

PAGE_SIZE = 10

dash.register_page(
    __name__,
    title="Data Portal - AEGIS",
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
                            "Explore ancient eDNA datasets for barley, wheat, rice, and their wild ancestors",
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
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Span(
                                            "⚙",
                                            style={
                                                "marginRight": "0.5rem",
                                                "opacity": "0.6",
                                            },
                                        ),
                                        "Filters",
                                    ],
                                    className="card-title",
                                    style={
                                        "fontSize": "0.85rem",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "0.08em",
                                        "color": "var(--aegis-text-muted)",
                                        "borderBottom": "1px solid var(--aegis-border-subtle)",
                                        "paddingBottom": "0.75rem",
                                        "marginBottom": "1rem",
                                    },
                                ),
                                html.Div(
                                    "Data Status",
                                    style={
                                        "fontSize": "0.8rem",
                                        "fontWeight": "600",
                                        "color": "var(--aegis-text-secondary)",
                                        "marginBottom": "0.75rem",
                                    },
                                ),
                                dbc.Checklist(id="checklist_input"),
                            ]
                        ),
                        className="filters-card",
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
    """Create a link to the species detail page."""
    return html.A(
        scientific_name,
        href=f"/data-portal/{tax_id}",
        style={
            "color": "var(--aegis-accent-primary)",
            "fontWeight": "500",
            "textDecoration": "none",
        },
    )


def return_badge_status(badge_text: str, color: str = None) -> dbc.Badge:
    """Create a status badge with appropriate color."""
    if color is not None:
        return dbc.Badge(badge_text, pill=True, color=color)

    color_map = {
        "Submitted to BioSamples": "secondary",
        "Raw Data - Submitted": "primary",
        "Assemblies - Submitted": "success",
        "Annotation Completed": "info",
        "Annotation - Submitted": "danger",
    }
    color = color_map.get(badge_text, "secondary")
    return dbc.Badge(badge_text, pill=True, color=color)


@callback(
    Output("data_table", "children"),
    Output("checklist_input", "options"),
    Output("pagination", "max_value"),
    Input("checklist_input", "value"),
    Input("input", "value"),
    Input("pagination", "active_page"),
    running=[
        (Output("input", "class_name"), "invisible", "visible"),
        (Output("pagination", "class_name"), "invisible", "justify-content-end"),
        (Output("filters-card", "class_name"), "invisible", "card-title"),
    ],
)
def create_update_data_table(filter_values, input_value, active_page):
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

    # Pagination params
    page = active_page or 1
    start = (page - 1) * PAGE_SIZE
    params["start"] = start
    params["size"] = PAGE_SIZE

    # Fetch
    response = requests.get(
        "https://aegis-be-1091670130981.europe-west2.run.app/data_portal",
        params=params,
        timeout=30,
    ).json()

    # Table
    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th(v)
                    for v in ["Scientific Name", "Common Name", "Current Status"]
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
        return empty_state, [], 1

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

    # Compute total pages from backend total
    total = response.get("total")
    if isinstance(total, dict):
        total = total.get("value")
    if not isinstance(total, int):
        total = len(results)
    max_pages = max(1, math.ceil(total / PAGE_SIZE))

    return table_container, options, max_pages
