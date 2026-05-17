"""Remove `<defs></defs>` when empty and `xmlns:xlink="..."` when unused."""

import re


def drop_empty_defs_and_unused_xlink(svg: str) -> str:
    """Remove `<defs></defs>` when empty and `xmlns:xlink="..."` when unused.

    drawsvg always emits a `<defs>` block, even when it contains
    nothing; gitsvg never references the xlink namespace today, so
    its declaration on the root is dead weight.

    Args:
        svg: The full SVG markup as a string.

    Returns:
        The SVG with empty `<defs>` and unused `xmlns:xlink` declarations removed.
    """
    svg = re.sub(r"<defs>\s*</defs>", "", svg)
    if not re.search(r"xlink:[a-zA-Z]+=", svg):
        svg = re.sub(r'\s+xmlns:xlink="[^"]*"', "", svg)
    return svg
