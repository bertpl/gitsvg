"""Draw a pull-request title pill anchored at the source-tip commit.

Mirrors `_branch_pill.py` in shape and styling, but anchored at the
*live* source-tip end of a branch rather than the static birth end:
the pill sits `theme.pull_request_pill_offset` pixels *above* the
source-tip commit in screen y (= towards the upper end of the commit
axis, opposite of where branch pills sit). The text is the PR's
`title`.

Width is approximated from the text length using a per-character pixel
estimate; no real glyph measurement.
"""

import drawsvg as draw

from gitsvg._theme import Theme
from gitsvg.layout import LayoutPullRequest
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y

# Classification (all four constants below): axis-symmetric — perceptual pill geometry, no grid-axis bias.
_PILL_PADDING_X = 12  # matches `_branch_pill._PILL_PADDING_X`
_PILL_PADDING_Y = 8  # matches `_branch_pill._PILL_PADDING_Y`
_PILL_CORNER_RADIUS = 4
_CHAR_WIDTH_FACTOR = 0.58  # rough char-width estimate at weight 500


def draw_pull_request_pill(
    d: draw.Drawing, pr: LayoutPullRequest, color: str, canvas: RenderCanvas, theme: Theme
) -> None:
    """Append a PR-title pill (background rectangle + text) to the drawing.

    Skips emission silently when `pr.title is None` — the caller is
    expected to gate on this, but the guard is here for safety.
    """
    if pr.title is None:
        return

    x = branch_axis_to_x(pr.from_branch_pos, canvas)
    y = commit_axis_to_y(pr.from_commit_pos, canvas) - theme.pull_request_pill_offset

    width = len(pr.title) * theme.branch_label_font_size * _CHAR_WIDTH_FACTOR + _PILL_PADDING_X
    height = theme.branch_label_font_size + _PILL_PADDING_Y

    d.append(
        draw.Rectangle(
            x - width / 2,
            y - height / 2,
            width,
            height,
            rx=_PILL_CORNER_RADIUS,
            ry=_PILL_CORNER_RADIUS,
            fill=color,
            opacity=theme.branch_label_bg_opacity,
        )
    )
    d.append(
        draw.Text(
            pr.title,
            theme.branch_label_font_size,
            x,
            y,
            text_anchor="middle",
            dominant_baseline="middle",
            fill="white",
            font_family=theme.label_font_family,
            font_weight="500",
        )
    )
