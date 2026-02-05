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
                            html.H1(
                                "API Documentation",
                                style={
                                    "fontFamily": "var(--font-display)",
                                    "fontSize": "2.5rem",
                                    "color": "var(--aegis-text-primary)",
                                    "marginBottom": "0.5rem",
                                },
                            ),
                            html.P(
                                "Programmatic access to ancient eDNA sequences, assemblies, and metadata",
                                style={
                                    "color": "var(--aegis-text-muted)",
                                    "marginBottom": "0",
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
                                html.Div(
                                    "🔗",
                                    style={
                                        "fontSize": "1.5rem",
                                        "marginBottom": "0.5rem",
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
                                    "aegis-be-*.run.app",
                                    style={
                                        "color": "var(--aegis-accent-primary)",
                                        "fontFamily": "var(--font-mono)",
                                        "fontSize": "0.85rem",
                                    },
                                ),
                            ],
                            style={
                                "padding": "1rem",
                                "background": "var(--aegis-bg-card)",
                                "borderRadius": "var(--radius-md)",
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
                                html.Div(
                                    "📄",
                                    style={
                                        "fontSize": "1.5rem",
                                        "marginBottom": "0.5rem",
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
                                "padding": "1rem",
                                "background": "var(--aegis-bg-card)",
                                "borderRadius": "var(--radius-md)",
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
                                html.Div(
                                    "🔓",
                                    style={
                                        "fontSize": "1.5rem",
                                        "marginBottom": "0.5rem",
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
                                "padding": "1rem",
                                "background": "var(--aegis-bg-card)",
                                "borderRadius": "var(--radius-md)",
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
                src="https://aegis-be-1091670130981.europe-west2.run.app/docs",
                style={
                    "display": "block",
                    "height": "calc(100vh - 250px)",
                    "minHeight": "600px",
                    "width": "100%",
                    "border": "none",
                    "overflow": "auto",
                    "borderRadius": "var(--radius-lg)",
                    "boxShadow": "var(--shadow-lg)",
                },
            ),
            style={
                "padding": "0 1.5rem 2rem 1.5rem",
            },
        ),
    ],
)
