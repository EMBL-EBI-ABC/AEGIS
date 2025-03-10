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
    dbc.Container(
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H1("AEGIS Data Portal", className="display-3",
                                    style={"textAlign": "center"}),
                            html.H2("Ancient Environmental Genomics Initiative for "
                                    "Sustainability", style={"textAlign": "center"}),
                        ]
                    ),
                    color="light",
                ),
                style={"marginTop": "15px"},
            )
        )
    ),
    style={
        'backgroundImage': f'url({BACKGROUND_URL})',
        'backgroundPosition': 'center',
        'backgroundRepeat': 'no-repeat',
        'background-size': 'cover',
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

                )
            ]
        )
    ]
)
