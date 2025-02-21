import dash
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    title = "Home",
    path="/"
)

layout = dbc.Row(
    dbc.Alert("Home Page", color="success"),
    className="p-5",
)
