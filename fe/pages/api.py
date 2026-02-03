import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(
    __name__,
    title="API",
)


def iframe_layout():
    return html.Iframe(
        src="https://aegis-be-1091670130981.europe-west2.run.app/redoc",
        style={
            "display": "block",
            "height": "100vh",
            "width": "100%",
            "border": "none",
            "border": "none",
            "overflow": "auto",
        },
    )


layout = dbc.Container(
    dbc.Row(
        dbc.Col(
            iframe_layout(),
            md=12,
        ),
    ),
    fluid=True,
    style={"backgroundColor": "white"},
)
