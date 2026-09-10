import dash_bootstrap_components as dbc
import os

CARTO_ATTRIBUTION = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
    'contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
)
_CARTO_LIGHT_URL = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
_ESRI_GRAY_URL = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/"
    "World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
)
_ESRI_ATTRIBUTION = (
    'Tiles &copy; <a href="https://www.esri.com/">Esri</a> &mdash; '
    'Esri, HERE, Garmin, &copy; OpenStreetMap contributors'
)

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


def basemap_props() -> dict:
    key = os.getenv("CARTO_API_KEY", "").strip()
    if key:
        return {"url": f"{_CARTO_LIGHT_URL}?key={key}", "attribution": CARTO_ATTRIBUTION}
    return {"url": _ESRI_GRAY_URL, "attribution": _ESRI_ATTRIBUTION}
