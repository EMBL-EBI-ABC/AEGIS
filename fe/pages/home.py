import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__, title="AEGIS - Ancient Environmental Genomics", path="/")


def feature_card(icon: str, title: str, description: str, button_text: str, href: str, variant: str = ""):
    """Create a feature card with icon, title, description and CTA button.

    `variant` picks one of the colour-blocked treatments inspired by
    aegisearth.bio (OUR VISION / OUR TEAM / OUR MISSION): "sand", "cream",
    "moss". An empty variant keeps the default white card.
    """
    modifier = f" feature-card--{variant}" if variant else ""
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
        className=f"feature-card{modifier}",
    )


def hero_section():
    """Create the hero banner section with animated background."""
    return html.Section(
        [
            html.Div(className="hero-network", **{"aria-hidden": "true"}),
            html.Img(
                src="/assets/aegis_logo_RGB_moss-charcoal_01.svg",
                className="hero-logo",
                alt="AEGIS",
            ),
            # The new brand logo does not bake in the byline; surface it as a
            # standalone caption so the hero still reads as the full identity.
            html.P(
                "Ancient Environmental Genomics Initiative for Sustainability",
                className="hero-byline",
            ),
        ],
        className="hero-banner",
    )


# Row 1: the three primary entry points.
_PRIMARY_FEATURES = [
    {
        "icon": "/assets/icons/data-portal.svg",
        "title": "Data Portal",
        "description": "Browse genomic data contributed by the AEGIS consortium. Filter by taxonomy, processing status, and more.",
        "button_text": "Explore Data",
        "href": "/data-portal",
        "variant": "sand",
    },
    {
        "icon": "/assets/icons/api-access.svg",
        "title": "API",
        "description": "Integrate AEGIS data into your bioinformatics pipelines. Raw sequences, assemblies, and metadata over REST.",
        "button_text": "View Documentation",
        "href": "/api",
        "variant": "cream",
    },
    {
        "icon": "/assets/icons/about-aegis.svg",
        "title": "About AEGIS",
        "description": "A global consortium directed from the Globe Institute, University of Copenhagen, working to unlock ancient genetic diversity for climate-resilient crops.",
        "button_text": "Learn More",
        "href": "/about",
        "variant": "moss",
    },
]

# Row 2: the two specialised programmatic clients, presented as a secondary tier.
_SECONDARY_FEATURES = [
    {
        "icon": "/assets/icons/mcp.svg",
        "title": "MCP Server",
        "description": "Connect any MCP-aware LLM client to search species, retrieve samples, and build downloads from a chat.",
        "button_text": "Open MCP Guide",
        "href": "/mcp",
        "variant": "sand",
    },
    {
        "icon": "/assets/icons/bulk-download.svg",
        "title": "Bulk Download",
        "description": "Use the aegis-download CLI to fetch raw reads, assemblies, annotations, and samples metadata in one go.",
        "button_text": "View CLI Docs",
        "href": "/bulk-download",
        "variant": "cream",
    },
]


def _feature_col(f, md=4):
    return dbc.Col(
        feature_card(
            icon=html.Img(
                src=f["icon"],
                style={"width": "2.25rem", "height": "2.25rem", "opacity": "0.85"},
            ),
            title=f["title"],
            description=f["description"],
            button_text=f["button_text"],
            href=f["href"],
            variant=f["variant"],
        ),
        md=md,
        className="mb-4",
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
                                    className="display-serif",
                                    style={"marginBottom": "1rem"},
                                ),
                                html.P(
                                    "AEGIS analyses ancient environmental DNA from soils, sediments, ice, and oceans alongside modern reference genomes to uncover how past ecosystems adapted to climate change - informing climate-resilient crops and biodiversity conservation.",
                                    style={
                                        "color": "var(--aegis-text-secondary)",
                                        "fontSize": "1.0625rem",
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
            # Three primary entry points on the first row.
            dbc.Row(
                [_feature_col(f) for f in _PRIMARY_FEATURES],
                className="g-4",
            ),
            # Two secondary tools on the second row, centred via an offset on
            # the first column so they sit beneath the middle of row 1 rather
            # than left-aligning into an unbalanced layout.
            dbc.Row(
                [
                    _feature_col(_SECONDARY_FEATURES[0], md={"size": 4, "offset": 2}),
                    _feature_col(_SECONDARY_FEATURES[1]),
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
                                        "fontFamily": "var(--font-body)",
                                        "fontSize": "1.25rem",
                                        "fontWeight": "500",
                                        "letterSpacing": "-0.01em",
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
