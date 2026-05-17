"""Drop whitespace that sits between SVG elements."""

import re


def strip_inter_element_whitespace(svg: str) -> str:
    """Drop whitespace that sits between elements (`>` followed by whitespace then `<`).

    Whitespace inside element content (e.g. between `<text>` and its
    first child character) is preserved — the regex only matches
    whitespace bounded by `>` on the left and `<` on the right, which
    is structurally inter-element.

    Args:
        svg: The full SVG markup as a string.

    Returns:
        The SVG with all inter-element whitespace removed.
    """
    return re.sub(r">\s+<", "><", svg)
