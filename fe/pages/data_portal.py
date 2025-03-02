import dash
from dash import callback, Output, Input, html
import dash_bootstrap_components as dbc
import pandas as pd
import requests

dash.register_page(
    __name__,
    title="Data Portal",
)

layout = dbc.Container(
    dbc.Row(
        [
            dbc.Col(md=3, id="data_filters"),
            dbc.Col(md=9, id="data_table")
        ],
        style={
            "margin-top": "15px",
        }
    )
)


@callback(
    Output("data_table", "children"),
    Input("data_table", "children"),
)
def create_update_data_table(input_value):
    response = requests.get(
        "https://aegis-be-1091670130981.europe-west2.run.app/data_portal").json()
    df = pd.DataFrame.from_records(response["results"],
                                   columns=["scientificName", "commonName",
                                            "currentStatus"])
    df.rename(columns={"scientificName": "Scientific Name", "commonName": "Common Name",
                       "currentStatus": "Current Status"}, inplace=True)
    return dbc.Table.from_dataframe(df=df, striped=True, bordered=True, hover=True,
                                    id="data_table")


@callback(
    Output("data_filters", "children"),
    Input("data_filters", "children"),
)
def create_update_data_filters(input_value):
    list_group_items = []
    response = requests.get(
        "https://aegis-be-1091670130981.europe-west2.run.app/data_portal").json()
    statuses = {"bioSamplesStatus": "Submitted to BioSamples",
                "rawDataStatus": "Raw Data submitted to ENA",
                "assembliesStatus": "Assemblies submitted to ENA"}
    for status_key, status_name in statuses.items():
        for bucket in response["aggregations"][status_key]["buckets"]:
            if bucket["key"] == "Done":
                list_group_items.append(
                    dbc.ListGroupItem(
                        html.Div(
                            [
                                html.Div(status_name),
                                html.Div(bucket["doc_count"])
                            ],
                            className="d-flex w-100 justify-content-between"
                        ),
                        action=True,
                        style={"cursor": "pointer"},
                    )
                )
    return dbc.Card(
        dbc.ListGroup(list_group_items),
        style={"marginBottom": "15px"},
    )
