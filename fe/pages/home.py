import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__, title="AEGIS - Ancient Environmental Genomics", path="/")


def feature_card(icon: str, title: str, description: str, button_text: str, href: str):
    """Create a feature card with icon, title, description and CTA button."""
    return html.Div(
        [
            html.Div(icon, className="feature-icon"),
            html.H4(title),
            html.P(description),
            dbc.Button(
                button_text,
                href=href,
                color="primary",
                className="mt-auto",
            ),
        ],
        className="feature-card",
    )


def hero_section():
    """Create the hero banner section with animated background."""
    return html.Section(
        [
            html.Img(
                src="/assets/aegis_logo-byline_RGB_black_01.png",
                className="hero-logo",
                alt="AEGIS - Ancient Environmental Genomics Initiative for Sustainability",
            ),
        ],
        className="hero-banner",
    )


def features_section():
    """Create the features grid section."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H2(
                                    "The past is a road map to a sustainable future",
                                    style={
                                        "fontFamily": "var(--font-display)",
                                        "color": "var(--aegis-text-primary)",
                                        "marginBottom": "0.5rem",
                                    },
                                ),
                                html.P(
                                    "AEGIS analyses ancient environmental DNA from soils, sediments, ice, and oceans alongside modern reference genomes to uncover how past ecosystems adapted to climate change - informing climate-resilient crops and biodiversity conservation.",
                                    style={
                                        "color": "var(--aegis-text-muted)",
                                        "maxWidth": "720px",
                                        "margin": "0 auto",
                                    },
                                ),
                            ],
                            className="text-center mb-5",
                        ),
                        md=12,
                    ),
                ],
            ),
            dbc.Row(
                [
                    dbc.Col(
                        feature_card(
                            icon=html.Img(
                                src="/assets/icons/data-portal.svg",
                                style={"width": "2.5rem", "height": "2.5rem", "opacity": "0.85"},
                            ),
                            title="Data Portal",
                            description="Browse genomic data contributed by the AEGIS consortium. Filter by taxonomy, processing status, and more.",
                            button_text="Explore Data",
                            href="/data-portal",
                        ),
                        md=4,
                        className="mb-4",
                    ),
                    dbc.Col(
                        feature_card(
                            icon=html.Img(
                                src="/assets/icons/api-access.svg",
                                style={"width": "2.5rem", "height": "2.5rem", "opacity": "0.85"},
                            ),
                            title="API Access",
                            description="Integrate AEGIS data into your bioinformatics pipelines. Access raw sequences, assemblies, and metadata programmatically.",
                            button_text="View Documentation",
                            href="/api",
                        ),
                        md=4,
                        className="mb-4",
                    ),
                    dbc.Col(
                        feature_card(
                            icon=html.Img(
                                src="/assets/icons/about-aegis.svg",
                                style={"width": "2.5rem", "height": "2.5rem", "opacity": "0.85"},
                            ),
                            title="About AEGIS",
                            description="A global consortium directed from the Globe Institute, University of Copenhagen, supported by the Novo Nordisk Foundation and the Wellcome Trust, working to unlock ancient genetic diversity for climate-resilient crops.",
                            button_text="Learn More",
                            href="/about",
                        ),
                        md=4,
                        className="mb-4",
                    ),
                ],
                className="g-4",
            ),
        ],
        className="py-5",
    )


def stats_section():
    """Create a statistics/highlights section."""
    stats = [
        {"value": "Ancient eDNA", "label": "Research Focus"},
        {"value": "18 Institutions", "label": "Global Consortium"},
        {"value": "Open Access", "label": "Data Policy"},
    ]

    return html.Section(
        dbc.Container(
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.Div(
                                    stat["value"],
                                    style={
                                        "fontFamily": "var(--font-display)",
                                        "fontSize": "1.5rem",
                                        "fontWeight": "500",
                                        "color": "var(--aegis-accent-primary)",
                                    },
                                ),
                                html.Div(
                                    stat["label"],
                                    style={
                                        "fontSize": "0.85rem",
                                        "color": "var(--aegis-text-muted)",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "0.08em",
                                    },
                                ),
                            ],
                            className="text-center py-4",
                        ),
                        md=4,
                    )
                    for stat in stats
                ],
            ),
            className="py-4",
        ),
        style={
            "background": "var(--aegis-bg-elevated)",
            "borderTop": "1px solid var(--aegis-border-subtle)",
            "borderBottom": "1px solid var(--aegis-border-subtle)",
        },
    )


layout = html.Div(
    [
        hero_section(),
        stats_section(),
        features_section(),
    ]
)
