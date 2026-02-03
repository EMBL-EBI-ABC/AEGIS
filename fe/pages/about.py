import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(
    __name__,
    title="About",
)

layout = dbc.Container(
    dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H3(
                            "Ancient environmental DNA provides solutions for "
                            "global food security challenges"
                        )
                    ),
                    dbc.CardImg(
                        src="https://www.embl.org/news/wp-content/uploads/2024/"
                        "06/2024-NNF-grant-ancient-plant-DNA-"
                        "1000x600-1.jpg",
                        top=True,
                    ),
                    dbc.CardBody(
                        [
                            html.H4("Summary"),
                            html.Ul(
                                [
                                    html.Li(
                                        "Through human cultivation, crop plants have lost the "
                                        "genetic diversity that was present in their wild-type "
                                        "ancestors"
                                    ),
                                    html.Li(
                                        "Ancient environmental DNA found in the soil can help "
                                        "researchers understand how the ancestors of crop "
                                        "plants adapted to historical climate change"
                                    ),
                                    html.Li(
                                        "These insights can be used to develop new strategies "
                                        "to make modern crops more resilient and provide novel "
                                        "solutions as climate change continues to threaten "
                                        "global food security"
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
            md={"width": 10, "offset": 1},
            style={"marginTop": "15px", "marginBottom": "15px"},
        )
    )
)
