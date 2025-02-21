import dash
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    title = "Data Portal",
)

layout = dbc.Row(
    dbc.Alert("Data Portal", color="success"),
    className="p-5",
)
