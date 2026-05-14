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
from gitsvg.render._geometry import offset_position
from gitsvg.render._metrics import _CHAR_WIDTH_FACTOR_NORMAL


def draw_pull_request_pill(
    d: draw.Drawing, pr: LayoutPullRequest, color: str, canvas: RenderCanvas, theme: Theme
) -> None:
    """Append a PR-title pill (background rectangle + text) to the drawing.

    Skips emission silently when `pr.title is None` — the caller is
    expected to gate on this, but the guard is here for safety.
    """
    if pr.title is None:
        return

    x, y = offset_position(
        anchor_branch_pos=pr.from_branch_pos,
        anchor_commit_pos=pr.from_commit_pos,
        branch_axis_offset_px=0,
        commit_axis_offset_px=-theme.pull_request_pill_offset,
        canvas=canvas,
    )

    width = len(pr.title) * theme.branch_label_font_size * _CHAR_WIDTH_FACTOR_NORMAL + theme.pill_padding_x
    height = theme.branch_label_font_size + theme.pill_padding_y
    corner = theme.pill_corner_radius

    d.append(
        draw.Rectangle(
            x - width / 2,
            y - height / 2,
            width,
            height,
            rx=corner,
            ry=corner,
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
