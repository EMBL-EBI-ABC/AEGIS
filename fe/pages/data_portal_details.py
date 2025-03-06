import dash
import requests
import json
from dash import html, Output, Input, callback, dcc
import dash_bootstrap_components as dbc
from .data_portal import return_badge_status
import time

dash.register_page(
    __name__,
    path_template="/data-portal/<tax_id>"
)


def layout(tax_id=None, **kwargs):
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    dbc.Spinner(
                        dbc.Card(dbc.CardBody(id="card", key=tax_id))
                    ),
                    md={"width": 10, "offset": 1},
                    style={"marginTop": "15px"},
                )
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                dbc.Tabs(id="tabs_header", active_tab="metadata_tab")
                            ),
                            dbc.CardBody(html.P(id="tabs_body", className="card-text")),
                        ],
                        id="tabs_card",
                    ),
                    md={"width": 10, "offset": 1},
                    style={"marginTop": "5px"},
                )
            ),
            dcc.Store(id='intermediate-value')
        ]
    )

def return_accession_button(accession: str) -> dbc.Button:
    return dbc.Button(
        accession,
        outline=True,
        href=f"https://www.ebi.ac.uk/biosamples/samples/{accession}")

@callback(
    Output("card", "children"),
    Output("tabs_header", "children"),
    Output("intermediate-value", "data"),
    Input("card", "key"),
    running=[
        (Output("tabs_card", "class_name"), "invisible",
         "visible"),
    ]
)
def create_data_portal_record(tax_id):
    time.sleep(2)
    response = requests.get(
        f"https://aegis-be-1091670130981.europe-west2.run.app/data_portal/{tax_id}"
    ).json()
    response = response["results"][0]
    children = [
        html.H3(response["scientificName"], className="card-title", id="header")]
    desc_list = html.Div([
        html.P(f"Tax ID: {response['taxId']}"),
        html.P(f"Scientific Name: {response['scientificName']}"),
        html.P(f"Common Name: {response['commonName']}"),
        html.P(["Current Status: ", return_badge_status(response["currentStatus"])]),
        html.P([
            "Kingdom: ",
            return_badge_status(response["phylogeny"]["kingdom"], "primary"),
            " -> ",
            "Phylum: ",
            return_badge_status(response["phylogeny"]["phylum"], "secondary"),
            " -> "
            "Class: ",
            return_badge_status(response["phylogeny"]["class"], "success"),
            " -> ",
            "Order: ",
            return_badge_status(response["phylogeny"]["order"], "warning"),
            " -> ",
            "Family: ",
            return_badge_status(response["phylogeny"]["family"], "danger"),
            " -> ",
            "Genus: ",
            return_badge_status(response["phylogeny"]["genus"], "info"),
        ])
    ])
    children.append(desc_list)

    tabs = [dbc.Tab(label="Metadata", tab_id="metadata_tab")]
    if len(response["rawData"]) > 0 or len(response["assemblies"]) > 0:
        tabs.append(dbc.Tab(label="Data", tab_id="data_tab"))
    return children, tabs, json.dumps(response["samples"])


@callback(
    Output("tabs_body", "children"),
    Input("tabs_header", "active_tab"),
    Input("intermediate-value", "data")
)
def create_tabs(active_tab, agg_data):
    agg_data = json.loads(agg_data)
    table_header = [
        html.Thead(html.Tr([html.Th(value) for value in
                            ["Accession", "Scientific Name", "Common Name", "Sex",
                             "Organism Part", "Current Status"]]))]
    table_body = [
        html.Tbody(
            [html.Tr(
                [html.Td(return_accession_button(row["accession"])),
                 html.Td(row["scientificName"]),
                 html.Td(row["commonName"]),
                 html.Td(row["sex"]),
                 html.Td(row["organismPart"]),
                 html.Td(return_badge_status(row["trackingSystem"]))])
                for
                row in agg_data])
    ]
    table = dbc.Table(table_header + table_body, striped=True, bordered=True,
                      hover=True, responsive=True)
    return table
