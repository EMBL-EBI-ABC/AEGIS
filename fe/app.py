import dash
from dash import html
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR], use_pages=True)

app.layout = [
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Data Portal",
                                    href=f"{dash.page_registry['pages.data_portal']
                                    ['path']}")),
            dbc.NavItem(dbc.NavLink("API",
                                    href=f"{dash.page_registry['pages.api']['path']}")),
            dbc.NavItem(dbc.NavLink("About",
                                    href=f"{dash.page_registry['pages.about']['path']}"
                                    )),
        ],
        brand="AEGIS",
        brand_href=f"{dash.page_registry['pages.home']['path']}",
        color="dark",
        dark=True,
    ),
    html.Div(dash.page_container)
]

if __name__ == "__main__":
    app.run_server(debug=True)
