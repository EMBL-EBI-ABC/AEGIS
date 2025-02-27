import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
import pandas as pd

dash.register_page(
    __name__,
    title="Home",
    path="/"
)

BACKGROUND_URL = ("https://www.embl.org/news/wp-content/uploads/2024/06/"
                  "2024-NNF-grant-ancient-plant-DNA-1000x600-1.jpg")

banner = html.Div(
    [
        html.H1("AEGIS Data Portal",
                className="display-3",
                style={
                    "color": "rgb(42, 62, 71)",
                    "textAlign": "center"
                }),
        html.P(
            "Ancient Environmental Genomics Initiative for Sustainability",
            style={
                "color": "rgb(42, 62, 71)",
                "fontSize": "2em",
                "textAlign": "center"
            }
        ),
    ],
    style={
        'backgroundImage': f'url({BACKGROUND_URL})',
        'backgroundPosition': 'center',
        'backgroundRepeat': 'no-repeat',
        'background-size': 'cover',
        'backgroundColor': 'rgb(255, 255, 255, 0.3)',
        'backgroundBlendMode': 'lighten',
        'height': '15em',
    }
)


def data_portal_card():
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4("Data Portal",
                            className="card-title"),
                    html.P("This is some card text",
                           className="card-text"),
                ]
            ),
            dbc.CardFooter(dbc.Button(
                "Data Portal",
                color="primary",
                href="/data-portal")),
        ]
    )


def api_card():
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4("API Documentation",
                            className="card-title"),
                    html.P("This is some card text",
                           className="card-text"),
                ]
            ),
            dbc.CardFooter(dbc.Button(
                "API Documentation",
                color="primary",
                href="/api")),
        ]
    )


def about_card():
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4("About",
                            className="card-title"),
                    html.P("This is some card text",
                           className="card-text"),
                ]
            ),
            dbc.CardFooter(dbc.Button(
                "About",
                color="primary",
                href="/about")),
        ]
    )


def sampling_map_card():
    df = pd.read_csv(
        "https://raw.githubusercontent.com/plotly/datasets/master/2011_february_us_airport_traffic.csv"
    )
    fig = px.scatter_map(df, lat="lat", lon="long", size="cnt", zoom=2,
                         template="plotly_dark")
    fig.update_traces(cluster=dict(enabled=True))
    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor="Black"
    )
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4("Sampling Map",
                        className="card-title"),
                dcc.Graph(figure=fig),
            ]
        )
    )


layout = html.Div(
    [
        banner,
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            data_portal_card(),
                            md=4,
                            style={"marginTop": "2em"}
                        ),
                        dbc.Col(
                            api_card(),
                            md=4,
                            style={"marginTop": "2em"}
                        ),
                        dbc.Col(
                            about_card(),
                            md=4,
                            style={"marginTop": "2em"},
                        ),
                    ]

                ),
                dbc.Row(
                    [
                        dbc.Col(
                            sampling_map_card(),
                            md=6,
                            className="offset-md-3",
                            style={
                                "marginTop": "2em",
                                "marginBottom": "2em",
                            },
                        ),
                    ]
                )
            ]
        )
    ]
)
