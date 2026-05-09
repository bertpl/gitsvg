"""Approximate text-width estimation for layout auto-fit.

These are rough character-count-based estimates (matching the
character-width factors the seed scripts and the renderer's pill
primitive use). They're good enough to keep labels inside the canvas
in v0.0.3 without measuring real glyph widths.
"""

from gitsvg._visual_constants import (
    BRANCH_LABEL_FONT_SIZE,
    HASH_FONT_SIZE,
    LABEL_FONT_SIZE,
)
from gitsvg.layout._layout import LayoutCommit

_NORMAL_CHAR_WIDTH_FACTOR = 0.58
_BOLD_CHAR_WIDTH_FACTOR = 0.64
_PILL_PADDING_X = 12  # matches the value in `gitsvg.render._primitives._branch_pill`


def pill_width(name: str) -> float:
    """Return the estimated pixel width of a branch-name pill rectangle."""
    return len(name) * BRANCH_LABEL_FONT_SIZE * _NORMAL_CHAR_WIDTH_FACTOR + _PILL_PADDING_X


def commit_label_width(commit: LayoutCommit) -> float:
    """Return the widest line's pixel width across a commit's label stack.

    Considers each `msg` line (split on `"\\n"`) at `LABEL_FONT_SIZE`,
    plus the optional `hash` line at `HASH_FONT_SIZE`. Bold weight (used
    when the commit is highlighted) widens characters by the bold
    factor.
    """
    if commit.msg is None and commit.hash is None:
        return 0.0
    msg_factor = _BOLD_CHAR_WIDTH_FACTOR if commit.highlight else _NORMAL_CHAR_WIDTH_FACTOR
    widest = 0.0
    if commit.msg is not None:
        for line in commit.msg.split("\n"):
            widest = max(widest, len(line) * LABEL_FONT_SIZE * msg_factor)
    if commit.hash is not None:
        widest = max(widest, len(commit.hash) * HASH_FONT_SIZE * _NORMAL_CHAR_WIDTH_FACTOR)
    return widest
