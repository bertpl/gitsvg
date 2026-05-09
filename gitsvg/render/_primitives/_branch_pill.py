"""Draw a branch-name pill at the branch's start point.

The pill is a filled rounded rectangle in the branch's colour with the
branch name in white text, positioned `BRANCH_NAME_PILL_OFFSET` pixels
*below* the branch's start point in screen y (= towards the lower end
of the commit axis, where pills sit at the branch's birth).

Width is approximated from the text length using a per-character pixel
estimate — the same approach the seed scripts used; we never measure
real glyph widths in v0.0.3.
"""

import drawsvg as draw

from gitsvg._visual_constants import (
    BRANCH_LABEL_BG_OPACITY,
    BRANCH_LABEL_FONT_SIZE,
    BRANCH_NAME_PILL_OFFSET,
    LABEL_FONT_FAMILY,
)
from gitsvg.layout import LayoutBranch
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y

_PILL_PADDING_X = 12  # extra width beyond the rendered text
_PILL_PADDING_Y = 8  # extra height beyond the font size
_PILL_CORNER_RADIUS = 4
_CHAR_WIDTH_FACTOR = 0.58  # rough char-width estimate at weight 500


def draw_branch_pill(d: draw.Drawing, branch: LayoutBranch, n_commits: int) -> None:
    """Append a branch-name pill (background rectangle + text) to the drawing."""
    x = branch_axis_to_x(branch.branch_pos)
    y = commit_axis_to_y(branch.start, n_commits) + BRANCH_NAME_PILL_OFFSET

    width = len(branch.name) * BRANCH_LABEL_FONT_SIZE * _CHAR_WIDTH_FACTOR + _PILL_PADDING_X
    height = BRANCH_LABEL_FONT_SIZE + _PILL_PADDING_Y

    d.append(
        draw.Rectangle(
            x - width / 2,
            y - height / 2,
            width,
            height,
            rx=_PILL_CORNER_RADIUS,
            ry=_PILL_CORNER_RADIUS,
            fill=branch.color,
            opacity=BRANCH_LABEL_BG_OPACITY,
        )
    )
    d.append(
        draw.Text(
            branch.name,
            BRANCH_LABEL_FONT_SIZE,
            x,
            y,
            text_anchor="middle",
            dominant_baseline="middle",
            fill="white",
            font_family=LABEL_FONT_FAMILY,
            font_weight="500",
        )
    )
