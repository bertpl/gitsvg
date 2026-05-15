"""Pixel-width helpers used by the auto-fit margin code and by the
label primitives that need a width before drawing.

Both functions delegate to :func:`gitsvg.render._glyph_metrics.text_width`,
which sizes geometry safely against every font in
``theme.label_font_family``'s fallback chain.
"""

from gitsvg.layout import LayoutCommit
from gitsvg.render._glyph_metrics import text_width
from gitsvg.theme import Theme


def pill_width(text: str, theme: Theme) -> float:
    """Return the estimated pixel width of a pill rectangle for `text`.

    Args:
        text: The pill's text content.
        theme: Supplies the font family, font size, and pill padding.

    Returns:
        Pixel width covering text plus padding on the leading edge.
    """
    return text_width(text, theme.label_font_family, theme.branch_label_font_size) + theme.pill_padding_x


def commit_label_width(commit: LayoutCommit, theme: Theme) -> float:
    """Return the widest line's pixel width across a commit's label stack.

    Considers each ``msg`` line (split on ``"\\n"``) at
    ``theme.label_font_size``, plus the optional ``hash`` line at
    ``theme.hash_font_size``. Bold weight (used when the commit is
    highlighted) routes through the bold-weight glyph metrics.

    Args:
        commit: The commit whose label stack is being measured.
        theme: Supplies font family and per-line font sizes.

    Returns:
        Pixel width of the widest line, or ``0`` if the commit has
        neither ``msg`` nor ``hash``.
    """
    if commit.msg is None and commit.hash is None:
        return 0.0
    widest = 0.0
    if commit.msg is not None:
        for line in commit.msg.split("\n"):
            widest = max(
                widest, text_width(line, theme.label_font_family, theme.label_font_size, bold=commit.highlight)
            )
    if commit.hash is not None:
        widest = max(widest, text_width(commit.hash, theme.label_font_family, theme.hash_font_size))
    return widest
