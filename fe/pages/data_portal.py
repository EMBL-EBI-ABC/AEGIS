import dash
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    title="Data Portal",
)

# layout = dbc.Row(
#     dbc.Alert("Data Portal", color="success"),
#     className="p-5",
# )

layout = dbc.Container(
    dbc.Row(
        [
            dbc.Col(
                dbc.Alert("Filter", color="success"),
                md=3
            ),
            dbc.Col(
                dbc.Alert("Table", color="success"),
                md=9
            )
        ],
        style={
            "margin-top": "15px",
        }
    )
)
