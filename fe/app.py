import dash
from dash import html
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,  # Base Bootstrap for component functionality
        "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500;9..144,600&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap",
    ],
    use_pages=True,
    suppress_callback_exceptions=True,
)

app.layout = html.Div(
    [
        html.Nav(
            dbc.Container(
                dbc.Row(
                    [
                        dbc.Col(
                            html.A(
                                [
                                    html.Span("AEGIS", className="brand-text"),
                                    html.Img(
                                        src="/assets/aegis_logomark_RGB_black_01.png",
                                        height="28px",
                                        className="brand-logo",
                                    ),
                                ],
                                href=f"{dash.page_registry['pages.home']['path']}",
                                className="navbar-brand d-flex align-items-center",
                            ),
                            width="auto",
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.A(
                                        "Data Portal",
                                        href=f"{dash.page_registry['pages.data_portal']['path']}",
                                        className="nav-link",
                                    ),
                                    html.A(
                                        "API",
                                        href=f"{dash.page_registry['pages.api']['path']}",
                                        className="nav-link",
                                    ),
                                    html.A(
                                        "About",
                                        href=f"{dash.page_registry['pages.about']['path']}",
                                        className="nav-link",
                                    ),
                                ],
                                className="d-flex gap-2",
                            ),
                            width="auto",
                            className="ms-auto",
                        ),
                    ],
                    align="center",
                    className="py-2",
                ),
                fluid=True,
            ),
            className="navbar",
        ),
        dash.page_container,
    ]
)

server = app.server

if __name__ == "__main__":
    app.run(debug=True)
