import dash
from dash import html
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.LITERA],
    use_pages=True)

app.layout = html.Div([
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
        brand=[
            "AEGIS",
            html.Img(
                src="/assets/aegis_logomark_RGB_black_01.png",
                height="30px",
                style={"marginLeft": "10px"},
            ),
        ],
        brand_href=f"{dash.page_registry['pages.home']['path']}",
        color="light",
        dark=False,
    ),
    dash.page_container
])
server = app.server

if __name__ == "__main__":
    app.run(debug=True)
