"""Remove attribute values that match SVG defaults."""

import re

# Pairs of `(attribute, default_value)`. Attributes carrying the listed value
# are removed from any element under `--small`. Both `400` and `normal` are
# valid SVG defaults for `font-weight`; we drop either form.
_DEFAULT_ATTRIBUTE_VALUES: list[tuple[str, str]] = [
    ("font-weight", "400"),
    ("font-weight", "normal"),
]


def drop_default_attribute_values(svg: str) -> str:
    """Remove attribute values that match SVG defaults.

    Today this drops `font-weight="400"` (or `="normal"`), the only
    explicit-default attribute drawsvg emits in our output. The lookup
    grows as future renderer changes surface more candidates.

    Args:
        svg: The full SVG markup as a string.

    Returns:
        The SVG with default-valued attributes removed.
    """
    for attr, default_value in _DEFAULT_ATTRIBUTE_VALUES:
        pattern = rf'\s+{re.escape(attr)}="{re.escape(default_value)}"'
        svg = re.sub(pattern, "", svg)
    return svg
