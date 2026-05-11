"""Draw a pull-request title pill anchored at the source-tip commit.

Mirrors `_branch_pill.py` in shape and styling, but anchored at the
*live* source-tip end of a branch rather than the static birth end:
the pill sits `PULL_REQUEST_PILL_OFFSET` pixels *above* the source-tip
commit in screen y (= towards the upper end of the commit axis,
opposite of where branch pills sit). The text is the PR's `title`.

Width is approximated from the text length using a per-character pixel
estimate; no real glyph measurement.
"""

import drawsvg as draw

from gitsvg._visual_constants import (
    BRANCH_LABEL_BG_OPACITY,
    BRANCH_LABEL_FONT_SIZE,
    LABEL_FONT_FAMILY,
    PULL_REQUEST_PILL_OFFSET,
)
from gitsvg.layout import LayoutCanvas, LayoutPullRequest
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y

_PILL_PADDING_X = 12  # matches `_branch_pill._PILL_PADDING_X`
_PILL_PADDING_Y = 8  # matches `_branch_pill._PILL_PADDING_Y`
_PILL_CORNER_RADIUS = 4
_CHAR_WIDTH_FACTOR = 0.58  # rough char-width estimate at weight 500


def draw_pull_request_pill(d: draw.Drawing, pr: LayoutPullRequest, canvas: LayoutCanvas) -> None:
    """Append a PR-title pill (background rectangle + text) to the drawing.

    Skips emission silently when `pr.title is None` — the caller is
    expected to gate on this, but the guard is here for safety.
    """
    if pr.title is None:
        return

    x = branch_axis_to_x(pr.from_branch_pos, canvas)
    y = commit_axis_to_y(pr.from_commit_pos, canvas) - PULL_REQUEST_PILL_OFFSET

    width = len(pr.title) * BRANCH_LABEL_FONT_SIZE * _CHAR_WIDTH_FACTOR + _PILL_PADDING_X
    height = BRANCH_LABEL_FONT_SIZE + _PILL_PADDING_Y

    d.append(
        draw.Rectangle(
            x - width / 2,
            y - height / 2,
            width,
            height,
            rx=_PILL_CORNER_RADIUS,
            ry=_PILL_CORNER_RADIUS,
            fill=pr.color,
            opacity=BRANCH_LABEL_BG_OPACITY,
        )
    )
    d.append(
        draw.Text(
            pr.title,
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
