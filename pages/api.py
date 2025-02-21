import dash
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    title = "API",
)

layout = dbc.Row(
    dbc.Alert("API", color="success"),
    className="p-5",
)
