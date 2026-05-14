"""Approximate text-width estimation and shared text/pill metrics.

A per-character pixel estimate matching the pill primitive's per-char
factor — no real glyph measurement. Good enough to keep labels inside
the canvas. Reads font sizes from the resolved theme.

The module-level constants here are also imported by the pill
primitives in `_primitives/`, so both halves of the rendering pipeline
(width estimation for auto-fit margins; actual pill drawing) draw from
a single source rather than maintaining duplicate copies.
"""

from gitsvg._theme import Theme
from gitsvg.layout import LayoutCommit

# Classification (all five constants below): axis-symmetric — perceptual text/pill geometry, no grid-axis bias.
_CHAR_WIDTH_FACTOR_NORMAL = 0.58  # rough char-width estimate at weight 500
_CHAR_WIDTH_FACTOR_BOLD = 0.64  # rough char-width estimate at weight 700
_PILL_PADDING_X = 12  # extra width beyond the rendered text
_PILL_PADDING_Y = 8  # extra height beyond the font size
_PILL_CORNER_RADIUS = 4
_LABEL_LINE_PADDING_PX = 4  # extra height per line in a multi-line label stack


def pill_width(name: str, theme: Theme) -> float:
    """Return the estimated pixel width of a branch-name pill rectangle."""
    return len(name) * theme.branch_label_font_size * _CHAR_WIDTH_FACTOR_NORMAL + _PILL_PADDING_X


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
