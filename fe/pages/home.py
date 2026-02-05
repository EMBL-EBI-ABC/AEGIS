import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__, title="Home", path="/")


def data_portal_card():
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4("Data Portal", className="card-title"),
                    html.P("Your entry point to search and explore all AEGIS projects data.", className="card-text"),
                ]
            ),
            dbc.CardFooter(
                dbc.Button("Data Portal", color="dark", href="/data-portal")
            ),
        ]
    )


def api_card():
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4("API Documentation", className="card-title"),
                    html.P("Access the same search functionality programmatically through our public API.", className="card-text"),
                ]
            ),
            dbc.CardFooter(
                dbc.Button("API Documentation", color="dark", href="/api")
            ),
        ]
    )


def about_card():
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4("About", className="card-title"),
                    html.P("Learn more about the AEGIS project and its mission.", className="card-text"),
                ]
            ),
            dbc.CardFooter(dbc.Button("About", color="dark", href="/about")),
        ]
    )


def banner_block() -> html.Div:
    return html.Div(
        [
            html.Div(
                style={
                    "width": "100%",
                    "height": "450px",
                    "background": "linear-gradient(to right, #808080, #ffffff, #808080)",
                },
            ),
            html.Img(
                src="/assets/aegis_logo-byline_RGB_black_01.png",
                style={
                    "position": "absolute",
                    "top": "50%",
                    "left": "50%",
                    "transform": "translate(-50%, -50%)",
                    "maxWidth": "650px",
                    "width": "80%",
                },
            ),
        ],
        style={"position": "relative", "width": "100%", "overflow": "hidden"},
        className="mb-4",
    )


layout = html.Div(
    [
        banner_block(),
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(data_portal_card(), md=4, style={"marginTop": "2em"}),
                        dbc.Col(api_card(), md=4, style={"marginTop": "2em"}),
                        dbc.Col(
                            about_card(),
                            md=4,
                            style={"marginTop": "2em"},
                        ),
                    ]
                )
            ]
        ),
    ]
)
