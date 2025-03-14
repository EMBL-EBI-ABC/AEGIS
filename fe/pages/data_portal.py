import dash
from dash import callback, Output, Input, html
import dash_bootstrap_components as dbc
import requests

dash.register_page(
    __name__,
    title="Data Portal",
)

layout = dbc.Container(
    dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Data Status", className="card-title"),
                            dbc.Checklist(id="checklist_input")
                        ]
                    )
                ),
                id="filters-card",
                md=3,
                style={"marginBottom": "5px"},
            ),
            dbc.Col(
                dbc.Spinner(
                    dbc.Stack(
                        [
                            dbc.Input(id="input", placeholder="Free text search, "
                                                              "ex. wheat...",
                                      type="text", debounce=True),
                            html.Div([
                                html.B("Statuses legend: "),
                                dbc.Badge("Submitted to Biosamples", pill=True,
                                          color="secondary"),
                                html.B(" -> "),
                                dbc.Badge("Raw Data - Submitted", pill=True,
                                          color="primary"),
                                html.B(" -> "),
                                dbc.Badge("Assemblies - Submitted", pill=True,
                                          color="success"),
                                html.B(" -> "),
                                dbc.Badge("Annotation Completed", pill=True,
                                          color="info"),
                                html.B(" -> "),
                                dbc.Badge("Annotation - Submitted", pill=True,
                                          color="danger"),
                            ]),
                            html.Div(id="data_table"),
                            dbc.Pagination(id="pagination", max_value=1,
                                           first_last=True,
                                           previous_next=True,
                                           fully_expanded=False),
                        ],
                        gap=3
                    )
                ),
                md=9),
        ],
        style={
            "marginTop": "15px",
        }
    )
)


def return_tax_id_button(scientific_name: str, tax_id: str) -> dbc.Button:
    return dbc.Button(
        scientific_name,
        outline=True,
        href=f"/data-portal/{tax_id}")


def return_badge_status(budge_text: str, color: str = None) -> dbc.Badge:
    if color is not None:
        return dbc.Badge(budge_text, pill=True, color=color)

    if budge_text == "Submitted to BioSamples":
        color = "secondary"
    elif budge_text == "Raw Data - Submitted":
        color = "primary"
    else:
        color = "success"
    return dbc.Badge(budge_text, pill=True, color=color)


@callback(
    Output("data_table", "children"),
    Output("checklist_input", "options"),
    Input("checklist_input", "value"),
    Input("input", "value"),
    Input("pagination", "active_page"),
    running=[
        (Output("input", "class_name"), "invisible",
         "visible"),
        (Output("pagination", "class_name"), "invisible",
         "justify-content-end"),
        (Output("filters-card", "class_name"), "invisible",
         "card-title")
    ]
)
def create_update_data_table(filter_values, input_value, pagination):
    statuses = {"bioSamplesStatus": "Submitted to BioSamples",
                "rawDataStatus": "Raw Data submitted to ENA",
                "assembliesStatus": "Assemblies submitted to ENA"}
    params = {}
    try:
        for value in filter_values:
            params[value] = "Done"
    except TypeError:
        pass
    if input_value is not None:
        params["q"] = input_value
    response = requests.get(
        "https://aegis-be-1091670130981.europe-west2.run.app/data_portal",
        params=params).json()

    table_header = [
        html.Thead(html.Tr([html.Th(value) for value in
                            ["Scientific Name", "Common Name", "Current Status"]]))]
    table_body = [
        html.Tbody(
            [html.Tr(
                [html.Td(return_tax_id_button(row["scientificName"], row["taxId"])),
                 html.Td(row["commonName"]),
                 html.Td(return_badge_status(row["currentStatus"]))])
                for
                row in response["results"]])
    ]
    table = dbc.Table(table_header + table_body, striped=True, bordered=True,
                      hover=True)

    options = []
    for status_key, status_name in statuses.items():
        for bucket in response["aggregations"][status_key]["buckets"]:
            if bucket["key"] == "Done":
                options.append(
                    {"label": f"{status_name} - {bucket['doc_count']}",
                     "value": status_key}
                )

    return table, options
