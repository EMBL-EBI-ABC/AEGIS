import os

import dash
from dash import html, dcc, callback, Input, Output, State, ctx
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

# Google Analytics (GA4). Defaults to the production property so deployments
# track without extra config; set GA_MEASUREMENT_ID="" to disable locally.
# In-app route changes are captured by GA4 Enhanced measurement ("page changes
# based on browser history events"), so no per-page tracking code is needed.
GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "G-0SGH92GYJE")

_GA_SNIPPET = (
    f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_MEASUREMENT_ID}');
    </script>
    """
    if GA_MEASUREMENT_ID
    else ""
)

app.index_string = f"""<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        {_GA_SNIPPET}
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>"""

_NAV_ITEMS = [
    ("Data Portal", "pages.data_portal"),
    ("API", "pages.api"),
    ("MCP", "pages.mcp"),
    ("Bulk Download", "pages.bulk_download"),
    ("About", "pages.about"),
]

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                html.Img(
                    src="/assets/aegis_logo_RGB_moss-charcoal_01.svg",
                    alt="AEGIS",
                    height="32px",
                    className="brand-logo",
                ),
                href=f"{dash.page_registry['pages.home']['path']}",
                className="navbar-brand d-flex align-items-center",
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavLink(
                            label,
                            href=f"{dash.page_registry[page_key]['path']}",
                            active="exact",
                        )
                        for label, page_key in _NAV_ITEMS
                    ],
                    navbar=True,
                    className="ms-auto",
                ),
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ],
        fluid=True,
    ),
    expand="lg",
    className="navbar",
)

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        navbar,
        html.Main(dash.page_container, className="page-main"),
        html.Footer(
            dbc.Container(
                html.Div(
                    [
                        html.P(
                            [
                                "AEGIS - Ancient Environmental Genomics Initiative for Sustainability",
                                html.Span(" | ", style={"opacity": "0.5"}),
                                html.A(
                                    "Visit aegisearth.bio ↗",
                                    href="https://aegisearth.bio/en",
                                    target="_blank",
                                    style={
                                        "color": "var(--aegis-text-inverse)",
                                        "textDecoration": "underline",
                                        "textUnderlineOffset": "3px",
                                    },
                                ),
                            ],
                            style={
                                "color": "var(--aegis-text-inverse)",
                                "marginBottom": "0.5rem",
                                "fontSize": "0.9rem",
                                "opacity": "0.92",
                            },
                        ),
                        html.P(
                            [
                                "Powered by ",
                                html.A(
                                    "EMBL-EBI",
                                    href="https://www.ebi.ac.uk/",
                                    target="_blank",
                                    style={
                                        "color": "var(--aegis-text-inverse)",
                                        "textDecoration": "underline",
                                        "textUnderlineOffset": "3px",
                                    },
                                ),
                            ],
                            style={
                                "color": "var(--aegis-text-inverse)",
                                "fontSize": "0.8rem",
                                "marginBottom": "0",
                                "opacity": "0.7",
                            },
                        ),
                    ],
                    className="text-center py-4",
                ),
            ),
            style={
                "background": "var(--aegis-accent-primary)",
                "marginTop": "auto",
            },
        ),
    ],
    className="page-shell",
)

server = app.server


@callback(
    Output("navbar-collapse", "is_open"),
    Input("navbar-toggler", "n_clicks"),
    Input("url", "pathname"),
    State("navbar-collapse", "is_open"),
    prevent_initial_call=True,
)
def _toggle_navbar(_n_clicks, _pathname, is_open):
    # Toggler click flips state; route changes always close the menu so a tap
    # on a nav link doesn't leave the dropdown hanging open behind the new page.
    if ctx.triggered_id == "navbar-toggler":
        return not is_open
    return False


if __name__ == "__main__":
    app.run(debug=True)
