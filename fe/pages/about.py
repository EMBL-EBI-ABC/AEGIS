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
        style={"padding": "1rem 0"},
    )


_PARTNERS = [
    ("University of Copenhagen", "Globe Institute · Denmark (lead)", "https://www.ku.dk/english/"),
    ("University of Cambridge", "United Kingdom", "https://www.cam.ac.uk/"),
    ("University of California, Berkeley", "United States", "https://www.berkeley.edu/"),
    ("Wellcome Sanger Institute", "United Kingdom", "https://www.sanger.ac.uk/"),
    ("EMBL-EBI", "European Bioinformatics Institute", "https://www.ebi.ac.uk/"),
    ("University of Colorado Boulder", "United States", "https://www.colorado.edu/"),
    ("Wageningen University & Research", "Netherlands", "https://www.wur.nl/en.htm"),
    ("Carlsberg Research Laboratory", "Denmark", "https://www.carlsbergfondet.dk/en/about-the-foundation/the-carlsberg-family/carlsberg-research-laboratory/"),
    ("Crop Science Centre", "Cambridge, United Kingdom", "https://www.cropsciencecentre.org/"),
    ("Seoul National University", "South Korea", "https://en.snu.ac.kr/"),
    ("Institut Pasteur", "France", "https://www.pasteur.fr/en"),
    ("NIAB", "United Kingdom", "https://www.niab.com/"),
    ("Agroscope", "Switzerland", "https://www.agroscope.admin.ch/agroscope/en/home.html"),
    ("University of Zürich", "Switzerland", "https://www.uzh.ch/en.html"),
    ("MARUM, University of Bremen", "Germany", "https://www.marum.de/en/"),
]


# Per-point styling: each chapter (01–04) gets its own colour-blocked panel,
# alternating sand / cream / moss / sand so the page reads as a series of
# editorial chapters rather than a stack of identical cards.
_KEY_POINTS = [
    {
        "number": "01",
        "title": "Lost Genetic Diversity",
        "body": (
            "Centuries of domestication have left today's crops with only a fraction of "
            "the genetic diversity present in their wild ancestors. Combined with reliance "
            "on uniform genetics and heavy inputs, this limits our ability to breed crops "
            "resilient to heat, drought, pests, and extreme weather."
        ),
        "variant": "sand",
    },
    {
        "number": "02",
        "title": "Ancient eDNA: A Window to the Past",
        "body": (
            "Environmental DNA preserved in soils, sediments, ice, and ocean cores can be "
            "thousands to millions of years old. By sequencing these fragments and comparing "
            "them to modern reference genomes, we identify genetic variants and beneficial "
            "species interactions that helped past ecosystems adapt to climate shifts."
        ),
        "variant": "cream",
    },
    {
        "number": "03",
        "title": "Ecosystem Modelling",
        "body": (
            "Beyond individual species, AEGIS uses ecosystem modelling to understand how "
            "combinations of species, including crops, microbiomes, and wild plants, created "
            "sustainable systems in the past. These insights inform modern agricultural "
            "practices."
        ),
        "variant": "moss",
    },
    {
        "number": "04",
        "title": "Open Data & Tools",
        "body": (
            "All genomic data is stored in the European Nucleotide Archive (ENA) and made "
            "publicly available through this portal. We're also developing new metadata "
            "checklists and bioinformatics tools for crop breeders, ecologists, and "
            "conservation biologists worldwide."
        ),
        "variant": "sand",
    },
]


_STATS = [
    ("18", "Institutions Worldwide"),
    ("Ancient eDNA", "Research Focus"),
    ("Open Access", "Data Policy"),
]


def _key_point(number: str, title: str, body: str, variant: str) -> html.Div:
    """One editorial 'chapter' panel — big serif number, sans heading, body copy."""
    return html.Div(
        [
            html.Div(
                number,
                style={
                    "fontFamily": "var(--font-display)",
                    "fontSize": "clamp(2.5rem, 5vw, 3.5rem)",
                    "fontWeight": "400",
                    "lineHeight": "1",
                    "marginBottom": "1rem",
                    "opacity": "0.9",
                },
            ),
            html.H3(
                title,
                style={
                    "fontSize": "clamp(1.25rem, 2vw, 1.5rem)",
                    "marginBottom": "0.75rem",
                },
            ),
            html.P(
                body,
                style={
                    "lineHeight": "1.7",
                    "marginBottom": "0",
                },
            ),
        ],
        className=f"feature-card feature-card--{variant}",
    )


def _stat_block(value: str, label: str) -> html.Div:
    return html.Div(
        [
            html.Div(
                value,
                style={
                    "fontFamily": "var(--font-body)",
                    "fontSize": "clamp(1.5rem, 3vw, 2rem)",
                    "fontWeight": "500",
                    "letterSpacing": "-0.01em",
                    "color": "var(--aegis-accent-primary)",
                    "marginBottom": "0.5rem",
                },
            ),
            html.Div(
                label,
                style={
                    "fontSize": "0.8rem",
                    "color": "var(--aegis-text-muted)",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.08em",
                },
            ),
        ],
        style={"padding": "1.5rem"},
    )


# Header band — eyebrow + display-serif H2, matches the home page treatment.
_header = html.Section(
    dbc.Container(
        html.Div(
            [
                html.Span("Our Mission", className="eyebrow"),
                html.H1(
                    "The past is a road map to a sustainable future",
                    className="display-serif",
                    style={"marginBottom": "1.5rem", "maxWidth": "920px"},
                ),
                html.P(
                    (
                        "AEGIS is a global consortium directed by Professor Eske Willerslev at the "
                        "Globe Institute, University of Copenhagen, supported by the Novo Nordisk "
                        "Foundation and the Wellcome Trust. By analysing ancient environmental DNA "
                        "from soils, sediments, ice, and oceans alongside modern reference genomes, "
                        "we uncover how past ecosystems adapted to climate change — to inform the "
                        "development of climate-resilient crops and stronger biodiversity conservation."
                    ),
                    style={
                        "fontSize": "1.0625rem",
                        "color": "var(--aegis-text-secondary)",
                        "lineHeight": "1.7",
                        "maxWidth": "780px",
                        "marginBottom": "0",
                    },
                ),
            ],
            className="py-5",
        ),
    ),
    style={
        "background": "var(--aegis-bg-deep)",
        "borderBottom": "1px solid var(--aegis-border-subtle)",
    },
)


_hero_image = html.Section(
    html.Img(
        src="https://www.embl.org/news/wp-content/uploads/2024/06/2024-NNF-grant-ancient-plant-DNA-1000x600-1.jpg",
        style={
            "width": "100%",
            "maxHeight": "420px",
            "objectFit": "cover",
            "display": "block",
        },
        alt="Ancient plant DNA research",
    ),
)


_stats_section = html.Section(
    dbc.Container(
        html.Div(
            [_stat_block(value, label) for value, label in _STATS],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
                "background": "var(--aegis-bg-sand)",
                "padding": "1rem",
            },
        ),
        className="py-5",
    ),
)


_key_points_section = html.Section(
    dbc.Container(
        [
            html.Div(
                [
                    html.Span("How We Work", className="eyebrow"),
                    html.H2(
                        "Four threads of inquiry",
                        className="display-serif",
                        style={
                            "fontSize": "clamp(1.75rem, 3.5vw, 2.75rem)",
                            "marginBottom": "0",
                            "maxWidth": "780px",
                        },
                    ),
                ],
                className="mb-5",
            ),
            html.Div(
                [
                    _key_point(p["number"], p["title"], p["body"], p["variant"])
                    for p in _KEY_POINTS
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(280px, 1fr))",
                    "gap": "1.5rem",
                },
            ),
        ],
        className="py-5",
    ),
    style={"background": "var(--aegis-bg-elevated)"},
)


_partners_section = html.Section(
    dbc.Container(
        [
            html.Div(
                [
                    html.Span("Consortium", className="eyebrow"),
                    html.H2(
                        "Collaborating institutions",
                        className="display-serif",
                        style={
                            "fontSize": "clamp(1.75rem, 3.5vw, 2.75rem)",
                            "marginBottom": "0",
                        },
                    ),
                ],
                className="mb-5",
            ),
            html.Div(
                [_partner_card(name, subtitle, href) for name, subtitle, href in _PARTNERS],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(240px, 1fr))",
                    "columnGap": "2rem",
                    "rowGap": "0",
                    "borderTop": "1px solid var(--aegis-border-subtle)",
                },
            ),
        ],
        className="py-5",
    ),
)


_funders_section = html.Section(
    dbc.Container(
        html.Div(
            [
                html.Span("Funded by", className="eyebrow"),
                html.Div(
                    [
                        html.A(
                            "Novo Nordisk Foundation",
                            href="https://novonordiskfonden.dk/en/",
                            target="_blank",
                            style={
                                "color": "var(--aegis-accent-primary)",
                                "fontSize": "1.25rem",
                                "fontFamily": "var(--font-display)",
                                "fontWeight": "400",
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
                                "fontSize": "1.25rem",
                                "fontFamily": "var(--font-display)",
                                "fontWeight": "400",
                            },
                        ),
                    ],
                ),
            ],
            className="py-4",
        ),
    ),
    style={
        "background": "var(--aegis-bg-deep)",
        "borderTop": "1px solid var(--aegis-border-subtle)",
    },
)


layout = html.Div(
    [
        _header,
        _hero_image,
        _stats_section,
        _key_points_section,
        _partners_section,
        _funders_section,
    ]
)
