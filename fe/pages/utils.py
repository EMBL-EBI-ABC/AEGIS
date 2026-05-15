import dash_bootstrap_components as dbc


def return_badge_status(badge_text: str, color: str = None) -> dbc.Badge:
    """Create a status badge with appropriate color."""
    if color is not None:
        return dbc.Badge(badge_text, pill=True, color=color)

    color_map = {
        "Submitted to BioSamples": "secondary",
        "Raw Data - Submitted": "primary",
        "Assemblies - Submitted": "info",
        "Annotation Complete": "success",
    }
    color = color_map.get(badge_text, "secondary")
    return dbc.Badge(badge_text, pill=True, color=color)
