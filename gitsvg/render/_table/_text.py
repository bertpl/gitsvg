"""Cell-text preparation for the table label layout — flatten + ellipsize.

Table cells are single-line and fixed-width, so each cell's text is first
flattened (any line breaks collapsed to spaces) and then truncated with a
trailing ellipsis if it doesn't fit the column — the same look a git GUI's
commit list gives an over-long subject. Pixel widths come from the shared
glyph-metrics machinery, so truncation respects the actual font.
"""

from gitsvg.render._glyph_metrics import text_width

_ELLIPSIS = "…"


def flatten_message(text: str) -> str:
    """Collapse a possibly multi-line string to a single line.

    Splits on universal newlines and rejoins with single spaces, so a
    multi-line commit message renders as one table-cell line.

    Args:
        text: The raw (possibly multi-line) text.

    Returns:
        The text with every line break replaced by a single space.
    """
    return " ".join(text.splitlines())


def fit_text(text: str, max_width: float, font_family: str, font_size: float, *, bold: bool = False) -> str:
    """Truncate `text` to `max_width` pixels, appending an ellipsis when clipped.

    Returns `text` unchanged when it already fits. Otherwise returns the
    longest prefix that, with a trailing ellipsis, fits within `max_width`
    (found by binary search on prefix length). When not even the ellipsis
    alone fits, returns an empty string.

    Args:
        text: The (already flattened) cell text.
        max_width: Available column width in pixels.
        font_family: CSS-style comma-separated font-family chain.
        font_size: Pixel font size.
        bold: Whether the text is bold (routes to bold glyph metrics).

    Returns:
        The text, or an ellipsized prefix, fitting within `max_width`.
    """

    def width(s: str) -> float:
        return text_width(s, font_family, font_size, bold=bold)

    if width(text) <= max_width:
        return text
    if width(_ELLIPSIS) > max_width:
        return ""

    # Largest k in [0, len(text)) with `text[:k] + ellipsis` fitting; width is
    # monotonic in k, so binary-search the boundary.
    lo, hi = 0, len(text) - 1
    best = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if width(text[:mid] + _ELLIPSIS) <= max_width:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return text[:best] + _ELLIPSIS
