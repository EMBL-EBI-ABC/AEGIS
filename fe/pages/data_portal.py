import dash
from dash import callback, Output, Input, html
import dash_bootstrap_components as dbc
import pandas as pd
import requests
import time

dash.register_page(
    __name__,
    title="Data Portal",
)

layout = dbc.Container(
    dbc.Row(
        [
            dbc.Col(md=3, id="data_filters"),
            dbc.Col(
                dbc.Spinner(
                    dbc.Stack(
                        [
                            dbc.Input(id="input", placeholder="Ex. wheat...",
                                      type="text", debounce=True),
                            html.Div(id="data_table"),
                            dbc.Pagination(id="pagination", max_value=1,
                                           first_last=True,
                                           previous_next=True,
                                           fully_expanded=False),
                        ],
                        gap=1
                    )
                ),
                md=9),
        ],
        style={
            "margin-top": "15px",
        }
    )
)


@callback(
    Output("data_table", "children"),
    Output("data_filters", "children"),
    Input("data_filters", "children"),
    Input("input", "value"),
    Input("pagination", "active_page"),
    running=[
        (Output("input", "class_name"), "invisible",
         "visible"),
        (Output("pagination", "class_name"), "invisible",
         "justify-content-end")
    ]
)
def create_update_data_table(filter_value, input_value, pagination):
    statuses = {"bioSamplesStatus": "Submitted to BioSamples",
                "rawDataStatus": "Raw Data submitted to ENA",
                "assembliesStatus": "Assemblies submitted to ENA"}
    params = {}
    if input_value is not None:
        params["q"] = input_value
    response = requests.get(
        "https://aegis-be-1091670130981.europe-west2.run.app/data_portal",
        params=params).json()
    df = pd.DataFrame.from_records(response["results"],
                                   columns=["scientificName", "commonName",
                                            "currentStatus"])
    df.rename(columns={"scientificName": "Scientific Name", "commonName": "Common Name",
                       "currentStatus": "Current Status"}, inplace=True)
    table = dbc.Table.from_dataframe(df=df, striped=True, bordered=True, hover=True,
                                     id="data_table")

    list_group_items = []
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
    filters = dbc.Card(
        dbc.CardBody([
            html.H4("Data Status", className="card-title"),
            dbc.ListGroup(list_group_items)
        ]),
        style={"marginBottom": "15px"})

    return table, filters
