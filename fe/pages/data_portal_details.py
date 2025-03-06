from typing import Callable

import dash
import requests
import json
from dash import html, Output, Input, callback, dcc
import dash_bootstrap_components as dbc

from .data_portal import return_badge_status

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
                            dbc.CardBody([
                                html.Div([
                                    html.B("Statuses legend: "),
                                    dbc.Badge("Submitted to Biosamples", pill=True,
                                              color="secondary"),
                                    html.B(" -> "),
                                    dbc.Badge("Raw Data - Submitted", pill=True,
                                              color="primary"),
                                    html.B(" -> "),
                                    dbc.Badge("Assemblies - Submitted", pill=True,
                                              color="success")
                                ],
                                    style={"marginBottom": "15px"},
                                ),
                                html.P(id="tabs_body", className="card-text")
                            ]),
                        ],
                        id="tabs_card",
                    ),
                    md={"width": 10, "offset": 1},
                    style={"marginTop": "5px", "marginBottom": "15px"},
                )
            ),
            dcc.Store(id='intermediate-value')
        ]
    )


def return_biosamples_accession_button(accession: str) -> dbc.Button:
    return dbc.Button(
        accession,
        outline=True,
        href=f"https://www.ebi.ac.uk/biosamples/samples/{accession}")


def return_ena_accession_button(accession: str) -> dbc.Button:
    return dbc.Button(
        accession,
        outline=True,
        href=f"https://www.ebi.ac.uk/ena/browser/view/{accession}")


def return_ftp_download_link(url: str) -> html.Div:
    links = []
    for link in url.split(";"):
        link_name = link.split('/')[-1]
        links.append(
            dbc.Button(
                link_name,
                outline=True,
                href=f"https://{link}")
        )
    return html.Div(links)


def return_table(column_names: list[str], field_names: list[str],
                 data: list[dict[str, str]],
                 field_function_mapping: dict[str, Callable]) -> dbc.Table:
    table_header = [html.Thead(html.Tr([html.Th(value) for value in column_names]))]
    table_body = [
        html.Tbody(
            [html.Tr(
                [html.Td(
                    field_function_mapping[field_name](row[field_name]) if
                    field_name in field_function_mapping
                    else row[field_name]) for field_name in field_names])
                for
                row in data])
    ]
    return dbc.Table(table_header + table_body, striped=True, bordered=True,
                     hover=True, responsive=True)


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
    if len(response["rawData"]) > 0:
        tabs.append(dbc.Tab(label="Raw Data", tab_id="raw_data_tab"))
    if len(response["assemblies"]) > 0:
        tabs.append(dbc.Tab(label="Assemblies", tab_id="assemblies_tab"))
    agg_data = {
        "samples": response["samples"],
        "rawData": response["rawData"],
        "assemblies": response["assemblies"],
    }
    return children, tabs, json.dumps(agg_data)


@callback(
    Output("tabs_body", "children"),
    Input("tabs_header", "active_tab"),
    Input("intermediate-value", "data")
)
def create_tabs(active_tab, agg_data):
    agg_data = json.loads(agg_data)
    if active_tab == "metadata_tab":
        field_function_mapping: dict[str, Callable] = {
            "accession": return_biosamples_accession_button,
            "trackingSystem": return_badge_status
        }
        return return_table(["Accession", "Scientific Name", "Common Name",
                             "Sex", "Organism Part", "Current Status"],
                            ["accession", "scientificName", "commonName", "sex",
                             "organismPart", "trackingSystem"], agg_data["samples"],
                            field_function_mapping)
    elif active_tab == "raw_data_tab":
        field_function_mapping: dict[str, Callable] = {
            "run_accession": return_ena_accession_button,
            "sample_accession": return_ena_accession_button,
            "experiment_accession": return_ena_accession_button,
            "study_accession": return_ena_accession_button,
            "fastq_ftp": return_ftp_download_link
        }
        return return_table(["Study Accession", "Sample Accession",
                             "Experiment Accession", "Run Accession", "FASTQ FTP"],
                            ["study_accession", "sample_accession",
                             "experiment_accession", "run_accession", "fastq_ftp"],
                            agg_data["rawData"], field_function_mapping)
    else:
        field_function_mapping: dict[str, Callable] = {
            "accession": return_ena_accession_button,
            "study_accession": return_ena_accession_button,
            "sample_accession": return_ena_accession_button
        }
        return return_table(["Accession", "Assembly Name", "Description",
                             "Study Accession", "Sample Accession", "Version"],
                            ["accession", "assembly_name",
                             "description", "study_accession", "sample_accession",
                             "version"],
                            agg_data["assemblies"], field_function_mapping)
