import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(
    __name__,
    title="About - AEGIS",
)

layout = dbc.Container(
    [
        # Page Header
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H1(
                            "About AEGIS",
                            style={
                                "fontFamily": "var(--font-display)",
                                "fontSize": "2.5rem",
                                "color": "var(--aegis-text-primary)",
                                "marginBottom": "0.5rem",
                            },
                        ),
                        html.P(
                            "Ancient Environmental Genomics Initiative for Sustainability",
                            style={
                                "color": "var(--aegis-accent-primary)",
                                "fontSize": "1.1rem",
                                "fontStyle": "italic",
                            },
                        ),
                    ],
                    className="pt-4 pb-3",
                ),
                md={"width": 10, "offset": 1},
            ),
        ),
        # Main Content Card
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        # Hero Image
                        html.Div(
                            html.Img(
                                src="https://www.embl.org/news/wp-content/uploads/2024/06/2024-NNF-grant-ancient-plant-DNA-1000x600-1.jpg",
                                style={
                                    "width": "100%",
                                    "height": "300px",
                                    "objectFit": "cover",
                                    "opacity": "0.9",
                                },
                            ),
                            style={
                                "overflow": "hidden",
                                "borderRadius": "var(--radius-lg) var(--radius-lg) 0 0",
                            },
                        ),
                        dbc.CardBody(
                            [
                                # Mission Statement
                                html.Div(
                                    [
                                        html.H2(
                                            "Unlocking Ancient Genetic Diversity for Climate-Resilient Crops",
                                            style={
                                                "fontFamily": "var(--font-display)",
                                                "fontSize": "1.75rem",
                                                "color": "var(--aegis-text-primary)",
                                                "marginBottom": "1rem",
                                                "lineHeight": "1.3",
                                            },
                                        ),
                                        html.P(
                                            "AEGIS is a seven-year, £66 million research initiative funded by the Novo Nordisk Foundation and Wellcome. By extracting DNA from ancient soil, ice, and sediment samples—some thousands to millions of years old—we're uncovering how crops like barley, wheat, and rice evolved and adapted to past climate changes.",
                                            style={
                                                "fontSize": "1.05rem",
                                                "color": "var(--aegis-text-secondary)",
                                                "lineHeight": "1.7",
                                                "marginBottom": "2rem",
                                            },
                                        ),
                                    ]
                                ),
                                # Funding Info
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    "£66M",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "fontSize": "1.75rem",
                                                        "fontWeight": "600",
                                                        "color": "var(--aegis-accent-primary)",
                                                    },
                                                ),
                                                html.Div(
                                                    "Total Funding",
                                                    style={
                                                        "fontSize": "0.8rem",
                                                        "color": "var(--aegis-text-muted)",
                                                        "textTransform": "uppercase",
                                                        "letterSpacing": "0.05em",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "textAlign": "center",
                                                "padding": "1rem",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.Div(
                                                    "7 Years",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "fontSize": "1.75rem",
                                                        "fontWeight": "600",
                                                        "color": "var(--aegis-earth-sage)",
                                                    },
                                                ),
                                                html.Div(
                                                    "Project Duration",
                                                    style={
                                                        "fontSize": "0.8rem",
                                                        "color": "var(--aegis-text-muted)",
                                                        "textTransform": "uppercase",
                                                        "letterSpacing": "0.05em",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "textAlign": "center",
                                                "padding": "1rem",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.Div(
                                                    "4+",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "fontSize": "1.75rem",
                                                        "fontWeight": "600",
                                                        "color": "var(--aegis-earth-terracotta)",
                                                    },
                                                ),
                                                html.Div(
                                                    "Partner Institutions",
                                                    style={
                                                        "fontSize": "0.8rem",
                                                        "color": "var(--aegis-text-muted)",
                                                        "textTransform": "uppercase",
                                                        "letterSpacing": "0.05em",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "textAlign": "center",
                                                "padding": "1rem",
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "grid",
                                        "gridTemplateColumns": "repeat(3, 1fr)",
                                        "background": "var(--aegis-bg-elevated)",
                                        "borderRadius": "var(--radius-md)",
                                        "marginBottom": "2rem",
                                    },
                                ),
                                # Key Points
                                html.Div(
                                    [
                                        # Point 1
                                        html.Div(
                                            [
                                                html.Div(
                                                    "01",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "fontSize": "2rem",
                                                        "fontWeight": "600",
                                                        "color": "var(--aegis-accent-primary)",
                                                        "marginBottom": "0.5rem",
                                                    },
                                                ),
                                                html.H4(
                                                    "Lost Genetic Diversity",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "color": "var(--aegis-text-primary)",
                                                        "marginBottom": "0.75rem",
                                                    },
                                                ),
                                                html.P(
                                                    "Through millennia of human cultivation, crop plants like barley, wheat, and rice have lost much of the genetic diversity present in their wild ancestors. This genetic bottleneck limits our ability to breed crops that can withstand climate change.",
                                                    style={
                                                        "color": "var(--aegis-text-secondary)",
                                                        "lineHeight": "1.7",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "padding": "1.5rem",
                                                "background": "var(--aegis-bg-elevated)",
                                                "borderRadius": "var(--radius-md)",
                                                "borderLeft": "3px solid var(--aegis-accent-primary)",
                                            },
                                        ),
                                        # Point 2
                                        html.Div(
                                            [
                                                html.Div(
                                                    "02",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "fontSize": "2rem",
                                                        "fontWeight": "600",
                                                        "color": "var(--aegis-earth-sage)",
                                                        "marginBottom": "0.5rem",
                                                    },
                                                ),
                                                html.H4(
                                                    "Ancient eDNA: A Window to the Past",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "color": "var(--aegis-text-primary)",
                                                        "marginBottom": "0.75rem",
                                                    },
                                                ),
                                                html.P(
                                                    "Environmental DNA preserved in soil, ice, and water samples can be thousands to millions of years old. By sequencing these fragments and comparing them to modern reference genomes, we can identify genetic variants that helped ancient plants survive past climate shifts.",
                                                    style={
                                                        "color": "var(--aegis-text-secondary)",
                                                        "lineHeight": "1.7",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "padding": "1.5rem",
                                                "background": "var(--aegis-bg-elevated)",
                                                "borderRadius": "var(--radius-md)",
                                                "borderLeft": "3px solid var(--aegis-earth-sage)",
                                            },
                                        ),
                                        # Point 3
                                        html.Div(
                                            [
                                                html.Div(
                                                    "03",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "fontSize": "2rem",
                                                        "fontWeight": "600",
                                                        "color": "var(--aegis-earth-terracotta)",
                                                        "marginBottom": "0.5rem",
                                                    },
                                                ),
                                                html.H4(
                                                    "Ecosystem Modelling",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "color": "var(--aegis-text-primary)",
                                                        "marginBottom": "0.75rem",
                                                    },
                                                ),
                                                html.P(
                                                    "Beyond individual species, AEGIS uses ecosystem modelling to understand how combinations of species—including crops, microbiomes, and wild plants—created sustainable systems in the past. These insights inform modern agricultural practices.",
                                                    style={
                                                        "color": "var(--aegis-text-secondary)",
                                                        "lineHeight": "1.7",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "padding": "1.5rem",
                                                "background": "var(--aegis-bg-elevated)",
                                                "borderRadius": "var(--radius-md)",
                                                "borderLeft": "3px solid var(--aegis-earth-terracotta)",
                                            },
                                        ),
                                        # Point 4
                                        html.Div(
                                            [
                                                html.Div(
                                                    "04",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "fontSize": "2rem",
                                                        "fontWeight": "600",
                                                        "color": "var(--aegis-earth-slate)",
                                                        "marginBottom": "0.5rem",
                                                    },
                                                ),
                                                html.H4(
                                                    "Open Data & Tools",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "color": "var(--aegis-text-primary)",
                                                        "marginBottom": "0.75rem",
                                                    },
                                                ),
                                                html.P(
                                                    "All genomic data is stored in the European Nucleotide Archive (ENA) and made publicly available through this portal. We're also developing new metadata standards and bioinformatics tools for crop breeders, ecologists, and conservation biologists worldwide.",
                                                    style={
                                                        "color": "var(--aegis-text-secondary)",
                                                        "lineHeight": "1.7",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "padding": "1.5rem",
                                                "background": "var(--aegis-bg-elevated)",
                                                "borderRadius": "var(--radius-md)",
                                                "borderLeft": "3px solid var(--aegis-earth-slate)",
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "gap": "1rem",
                                    },
                                ),
                            ],
                            style={"padding": "2rem"},
                        ),
                    ],
                    style={
                        "background": "var(--aegis-bg-card)",
                        "border": "1px solid var(--aegis-border-subtle)",
                        "overflow": "hidden",
                    },
                ),
                md={"width": 10, "offset": 1},
                style={"marginBottom": "2rem"},
            )
        ),
        # Partners Section
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H3(
                                "Collaborating Institutions",
                                style={
                                    "fontFamily": "var(--font-display)",
                                    "color": "var(--aegis-text-primary)",
                                    "marginBottom": "1.5rem",
                                    "textAlign": "center",
                                },
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.A(
                                                "EMBL-EBI",
                                                href="https://www.ebi.ac.uk/",
                                                target="_blank",
                                                style={
                                                    "color": "var(--aegis-accent-primary)",
                                                    "fontWeight": "500",
                                                },
                                            ),
                                            html.Br(),
                                            html.Span(
                                                "European Bioinformatics Institute",
                                                style={
                                                    "fontSize": "0.8rem",
                                                    "color": "var(--aegis-text-muted)",
                                                },
                                            ),
                                        ],
                                        style={
                                            "textAlign": "center",
                                            "padding": "1rem",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.A(
                                                "University of Copenhagen",
                                                href="https://www.ku.dk/english/",
                                                target="_blank",
                                                style={
                                                    "color": "var(--aegis-accent-primary)",
                                                    "fontWeight": "500",
                                                },
                                            ),
                                            html.Br(),
                                            html.Span(
                                                "Globe Institute",
                                                style={
                                                    "fontSize": "0.8rem",
                                                    "color": "var(--aegis-text-muted)",
                                                },
                                            ),
                                        ],
                                        style={
                                            "textAlign": "center",
                                            "padding": "1rem",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.A(
                                                "University of Cambridge",
                                                href="https://www.cam.ac.uk/",
                                                target="_blank",
                                                style={
                                                    "color": "var(--aegis-accent-primary)",
                                                    "fontWeight": "500",
                                                },
                                            ),
                                            html.Br(),
                                            html.Span(
                                                "Department of Genetics",
                                                style={
                                                    "fontSize": "0.8rem",
                                                    "color": "var(--aegis-text-muted)",
                                                },
                                            ),
                                        ],
                                        style={
                                            "textAlign": "center",
                                            "padding": "1rem",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.A(
                                                "Wellcome Sanger Institute",
                                                href="https://www.sanger.ac.uk/",
                                                target="_blank",
                                                style={
                                                    "color": "var(--aegis-accent-primary)",
                                                    "fontWeight": "500",
                                                },
                                            ),
                                            html.Br(),
                                            html.Span(
                                                "Genome Research",
                                                style={
                                                    "fontSize": "0.8rem",
                                                    "color": "var(--aegis-text-muted)",
                                                },
                                            ),
                                        ],
                                        style={
                                            "textAlign": "center",
                                            "padding": "1rem",
                                        },
                                    ),
                                ],
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(auto-fit, minmax(200px, 1fr))",
                                    "gap": "1rem",
                                },
                            ),
                        ]
                    ),
                    style={
                        "background": "var(--aegis-bg-card)",
                        "border": "1px solid var(--aegis-border-subtle)",
                    },
                ),
                md={"width": 10, "offset": 1},
                style={"marginBottom": "2rem"},
            )
        ),
        # Funders Section
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.P(
                            "Funded by",
                            style={
                                "color": "var(--aegis-text-muted)",
                                "marginBottom": "0.75rem",
                                "fontSize": "0.85rem",
                                "textTransform": "uppercase",
                                "letterSpacing": "0.05em",
                            },
                        ),
                        html.Div(
                            [
                                html.A(
                                    "Novo Nordisk Foundation",
                                    href="https://novonordiskfonden.dk/en/",
                                    target="_blank",
                                    style={
                                        "color": "var(--aegis-accent-primary)",
                                        "fontSize": "1.1rem",
                                        "fontFamily": "var(--font-display)",
                                        "fontWeight": "500",
                                    },
                                ),
                                html.Span(
                                    "  &  ",
                                    style={"color": "var(--aegis-text-muted)"},
                                ),
                                html.A(
                                    "Wellcome",
                                    href="https://wellcome.org/",
                                    target="_blank",
                                    style={
                                        "color": "var(--aegis-accent-primary)",
                                        "fontSize": "1.1rem",
                                        "fontFamily": "var(--font-display)",
                                        "fontWeight": "500",
                                    },
                                ),
                            ],
                        ),
                    ],
                    className="text-center py-4",
                ),
                md={"width": 10, "offset": 1},
            )
        ),
    ],
    className="pb-5",
)
