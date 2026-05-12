"""Approximate text-width estimation for auto-fit margin computation.

A per-character pixel estimate matching the pill primitive's per-char
factor — no real glyph measurement. Good enough to keep labels inside
the canvas. Reads font sizes from the resolved theme.
"""

from gitsvg.layout import LayoutCommit
from gitsvg.render._theme import Theme

_NORMAL_CHAR_WIDTH_FACTOR = 0.58
_BOLD_CHAR_WIDTH_FACTOR = 0.64
_PILL_PADDING_X = 12  # matches the value in `gitsvg.render._primitives._branch_pill`


def pill_width(name: str, theme: Theme) -> float:
    """Return the estimated pixel width of a branch-name pill rectangle."""
    return len(name) * theme.branch_label_font_size * _NORMAL_CHAR_WIDTH_FACTOR + _PILL_PADDING_X


def commit_label_width(commit: LayoutCommit, theme: Theme) -> float:
    """Return the widest line's pixel width across a commit's label stack.

    Considers each `msg` line (split on `"\\n"`) at
    `theme.label_font_size`, plus the optional `hash` line at
    `theme.hash_font_size`. Bold weight (used when the commit is
    highlighted) widens characters by the bold factor.
    """
    if commit.msg is None and commit.hash is None:
        return 0.0
    msg_factor = _BOLD_CHAR_WIDTH_FACTOR if commit.highlight else _NORMAL_CHAR_WIDTH_FACTOR
    widest = 0.0
    if commit.msg is not None:
        for line in commit.msg.split("\n"):
            widest = max(widest, len(line) * theme.label_font_size * msg_factor)
    if commit.hash is not None:
        widest = max(widest, len(commit.hash) * theme.hash_font_size * _NORMAL_CHAR_WIDTH_FACTOR)
    return widest
