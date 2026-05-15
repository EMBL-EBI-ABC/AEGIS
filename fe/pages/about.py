import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(
    __name__,
    title="About - AEGIS",
)


def _partner_card(name: str, subtitle: str, href: str) -> html.Div:
    return html.Div(
        [
            html.A(
                name,
                href=href,
                target="_blank",
                style={
                    "color": "var(--aegis-accent-primary)",
                    "fontWeight": "500",
                },
            ),
            html.Br(),
            html.Span(
                subtitle,
                style={
                    "fontSize": "0.8rem",
                    "color": "var(--aegis-text-muted)",
                },
            ),
        ],
        style={"textAlign": "center", "padding": "1rem"},
    )


_PARTNERS = [
    ("University of Copenhagen", "Globe Institute · Denmark (lead)", "https://www.ku.dk/english/"),
    ("University of Cambridge", "United Kingdom", "https://www.cam.ac.uk/"),
    ("University of California, Berkeley", "United States", "https://www.berkeley.edu/"),
    ("Wellcome Sanger Institute", "United Kingdom", "https://www.sanger.ac.uk/"),
    ("EMBL-EBI", "European Bioinformatics Institute", "https://www.ebi.ac.uk/"),
    ("University of Colorado Boulder", "United States", "https://www.colorado.edu/"),
    ("Wageningen University & Research", "Netherlands", "https://www.wur.nl/en.htm"),
    ("Carlsberg Research Laboratory", "Denmark", "https://www.carlsbergresearchlaboratory.com/"),
    ("Crop Science Centre", "Cambridge, United Kingdom", "https://www.cropsciencecentre.org/"),
    ("Seoul National University", "South Korea", "https://en.snu.ac.kr/"),
    ("Institut Pasteur", "France", "https://www.pasteur.fr/en"),
    ("NIAB", "United Kingdom", "https://www.niab.com/"),
    ("Agroscope", "Switzerland", "https://www.agroscope.admin.ch/agroscope/en/home.html"),
    ("University of Zürich", "Switzerland", "https://www.uzh.ch/en.html"),
    ("MARUM, University of Bremen", "Germany", "https://www.marum.de/en/"),
]

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
                                            "The past is a road map to a sustainable future",
                                            style={
                                                "fontFamily": "var(--font-display)",
                                                "fontSize": "1.75rem",
                                                "color": "var(--aegis-text-primary)",
                                                "marginBottom": "1rem",
                                                "lineHeight": "1.3",
                                            },
                                        ),
                                        html.P(
                                            "AEGIS is a global consortium directed by Professor Eske Willerslev at the Globe Institute, University of Copenhagen, supported by the Novo Nordisk Foundation and the Wellcome Trust. By analysing ancient environmental DNA from soils, sediments, ice, and oceans alongside modern reference genomes, we uncover how past ecosystems adapted to climate change - to inform the development of climate-resilient crops and stronger biodiversity conservation.",
                                            style={
                                                "fontSize": "1.05rem",
                                                "color": "var(--aegis-text-secondary)",
                                                "lineHeight": "1.7",
                                                "marginBottom": "2rem",
                                            },
                                        ),
                                    ]
                                ),
                                # Headline stats
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    "18",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "fontSize": "1.75rem",
                                                        "fontWeight": "600",
                                                        "color": "var(--aegis-accent-primary)",
                                                    },
                                                ),
                                                html.Div(
                                                    "Institutions Worldwide",
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
                                                    "Ancient eDNA",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "fontSize": "1.75rem",
                                                        "fontWeight": "600",
                                                        "color": "var(--aegis-earth-sage)",
                                                    },
                                                ),
                                                html.Div(
                                                    "Research Focus",
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
                                                    "Open Access",
                                                    style={
                                                        "fontFamily": "var(--font-display)",
                                                        "fontSize": "1.75rem",
                                                        "fontWeight": "600",
                                                        "color": "var(--aegis-earth-terracotta)",
                                                    },
                                                ),
                                                html.Div(
                                                    "Data Policy",
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
                                                    "Centuries of domestication have left today's crops with only a fraction of the genetic diversity present in their wild ancestors. Combined with reliance on uniform genetics and heavy inputs, this limits our ability to breed crops resilient to heat, drought, pests, and extreme weather.",
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
                                                    "Environmental DNA preserved in soils, sediments, ice, and ocean cores can be thousands to millions of years old. By sequencing these fragments and comparing them to modern reference genomes, we identify genetic variants and beneficial species interactions that helped past ecosystems adapt to climate shifts.",
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
                                                    "Beyond individual species, AEGIS uses ecosystem modelling to understand how combinations of species, including crops, microbiomes, and wild plants, created sustainable systems in the past. These insights inform modern agricultural practices.",
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
                                                    "All genomic data is stored in the European Nucleotide Archive (ENA) and made publicly available through this portal. We're also developing new metadata checklists and bioinformatics tools for crop breeders, ecologists, and conservation biologists worldwide.",
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
                                [_partner_card(name, subtitle, href) for name, subtitle, href in _PARTNERS],
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(auto-fit, minmax(220px, 1fr))",
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
