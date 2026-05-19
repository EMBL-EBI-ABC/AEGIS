import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(
    __name__,
    title="API Documentation - AEGIS",
)

layout = html.Div(
    [
        # Header
        dbc.Container(
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            html.Span("Integrate", className="eyebrow"),
                            html.H1(
                                "API Documentation",
                                style={"marginBottom": "0.75rem"},
                            ),
                            html.P(
                                "Programmatic access to AEGIS genomic data, assemblies, and sample metadata.",
                                style={
                                    "color": "var(--aegis-text-secondary)",
                                    "marginBottom": "0",
                                    "maxWidth": "640px",
                                },
                            ),
                        ],
                        className="pt-4 pb-3",
                    ),
                ),
            ),
        ),
        # API Info Cards
        dbc.Container(
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.Img(
                                    src="/assets/icons/base-url.svg",
                                    style={
                                        "width": "1.75rem",
                                        "height": "1.75rem",
                                        "marginBottom": "0.5rem",
                                        "opacity": "0.85",
                                    },
                                ),
                                html.Div(
                                    "Base URL",
                                    style={
                                        "fontSize": "0.75rem",
                                        "color": "var(--aegis-text-muted)",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "0.05em",
                                    },
                                ),
                                html.Code(
                                    "portal.aegisearth.bio/api",
                                    style={
                                        "color": "var(--aegis-accent-primary)",
                                        "fontFamily": "var(--font-mono)",
                                        "fontSize": "0.85rem",
                                    },
                                ),
                            ],
                            style={
                                "padding": "1.25rem",
                                "background": "var(--aegis-bg-card)",
                                "border": "1px solid var(--aegis-border-subtle)",
                                "textAlign": "center",
                            },
                        ),
                        md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Img(
                                    src="/assets/icons/format.svg",
                                    style={
                                        "width": "1.75rem",
                                        "height": "1.75rem",
                                        "marginBottom": "0.5rem",
                                        "opacity": "0.85",
                                    },
                                ),
                                html.Div(
                                    "Format",
                                    style={
                                        "fontSize": "0.75rem",
                                        "color": "var(--aegis-text-muted)",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "0.05em",
                                    },
                                ),
                                html.Code(
                                    "REST / JSON",
                                    style={
                                        "color": "var(--aegis-accent-primary)",
                                        "fontFamily": "var(--font-mono)",
                                        "fontSize": "0.85rem",
                                    },
                                ),
                            ],
                            style={
                                "padding": "1.25rem",
                                "background": "var(--aegis-bg-card)",
                                "border": "1px solid var(--aegis-border-subtle)",
                                "textAlign": "center",
                            },
                        ),
                        md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Img(
                                    src="/assets/icons/auth.svg",
                                    style={
                                        "width": "1.75rem",
                                        "height": "1.75rem",
                                        "marginBottom": "0.5rem",
                                        "opacity": "0.85",
                                    },
                                ),
                                html.Div(
                                    "Authentication",
                                    style={
                                        "fontSize": "0.75rem",
                                        "color": "var(--aegis-text-muted)",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "0.05em",
                                    },
                                ),
                                html.Code(
                                    "None required",
                                    style={
                                        "color": "var(--aegis-earth-sage)",
                                        "fontFamily": "var(--font-mono)",
                                        "fontSize": "0.85rem",
                                    },
                                ),
                            ],
                            style={
                                "padding": "1.25rem",
                                "background": "var(--aegis-bg-card)",
                                "border": "1px solid var(--aegis-border-subtle)",
                                "textAlign": "center",
                            },
                        ),
                        md=4,
                        className="mb-3",
                    ),
                ],
                className="mb-4",
            ),
        ),
        # Swagger UI Iframe
        html.Div(
            html.Iframe(
                src="https://portal.aegisearth.bio/api/docs",
                style={
                    "display": "block",
                    "height": "calc(100vh - 250px)",
                    "minHeight": "600px",
                    "width": "100%",
                    "border": "1px solid var(--aegis-border-subtle)",
                    "overflow": "auto",
                    "borderRadius": "0",
                    "boxShadow": "none",
                },
            ),
            style={
                "padding": "0 1.5rem 2rem 1.5rem",
            },
        ),
    ],
)
