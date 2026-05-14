"""Approximate label-width estimation used by the auto-fit margin
code and by the label primitives that need a pixel width before drawing.

A per-character pixel estimate — no real glyph measurement. Good
enough to keep labels inside the canvas. Reads font sizes and pill
geometry off the resolved theme.
"""

from gitsvg.layout import LayoutCommit
from gitsvg.theme import Theme

# Classification (both factors): axis-symmetric — perceptual char-width
# estimates, no grid-axis bias.
_CHAR_WIDTH_FACTOR_NORMAL = 0.58  # rough char-width estimate at weight 500
_CHAR_WIDTH_FACTOR_BOLD = 0.64  # rough char-width estimate at weight 700


def pill_width(text: str, theme: Theme) -> float:
    """Return the estimated pixel width of a pill rectangle for `text`."""
    return len(text) * theme.branch_label_font_size * _CHAR_WIDTH_FACTOR_NORMAL + theme.pill_padding_x


def commit_label_width(commit: LayoutCommit, theme: Theme) -> float:
    """Return the widest line's pixel width across a commit's label stack.

    Considers each `msg` line (split on `"\\n"`) at
    `theme.label_font_size`, plus the optional `hash` line at
    `theme.hash_font_size`. Bold weight (used when the commit is
    highlighted) widens characters by the bold factor.
    """
    if commit.msg is None and commit.hash is None:
        return 0.0
    msg_factor = _CHAR_WIDTH_FACTOR_BOLD if commit.highlight else _CHAR_WIDTH_FACTOR_NORMAL
    widest = 0.0
    if commit.msg is not None:
        for line in commit.msg.split("\n"):
            widest = max(widest, len(line) * theme.label_font_size * msg_factor)
    if commit.hash is not None:
        widest = max(widest, len(commit.hash) * theme.hash_font_size * _CHAR_WIDTH_FACTOR_NORMAL)
    return widest
