import dash
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    title = "About",
)

layout = dbc.Row(
    dbc.Alert("About Page", color="success"),
    className="p-5",
)
