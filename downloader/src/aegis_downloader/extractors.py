import re


_SLUG_RE = re.compile(r"[^a-zA-Z0-9]+")


def slugify(name: str) -> str:
    return _SLUG_RE.sub("_", name).strip("_").lower()
