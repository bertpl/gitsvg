"""Shorten 6-digit hex colour values to 3-digit form when pair-wise digits match."""

import re

# Match `#RRGGBB` only when not followed by another hex digit (otherwise
# `#abcdef0` would shorten its first six characters to `#abc`, corrupting
# the value).
_HEX_RE = re.compile(r"#([0-9A-Fa-f])([0-9A-Fa-f])([0-9A-Fa-f])([0-9A-Fa-f])([0-9A-Fa-f])([0-9A-Fa-f])(?![0-9A-Fa-f])")


def shorten_hex_colors(svg: str) -> str:
    """Rewrite `#RRGGBB` hex colour values to `#RGB` when pair-wise digits match.

    `#aabbcc` becomes `#abc` (3 bytes saved per match); `#aabbcd` stays
    unchanged. Case-preserving: `#AABBCC` → `#ABC`. The trailing
    lookahead guards against matching the first six characters of a
    longer hex string.

    Args:
        svg: The full SVG markup as a string.

    Returns:
        The SVG with eligible hex colours shortened.
    """

    def _replace(match: re.Match[str]) -> str:
        r1, r2, g1, g2, b1, b2 = match.groups()
        if r1 == r2 and g1 == g2 and b1 == b2:
            return f"#{r1}{g1}{b1}"
        return match.group(0)

    return _HEX_RE.sub(_replace, svg)
