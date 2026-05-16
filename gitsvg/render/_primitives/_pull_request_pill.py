"""Draw a pull-request title pill anchored at the projected merge corner.

The world anchor point is the **phantom point on the source branch's
lane at the projected merge target's commit-axis position** —
`(branch_pos = pr.from_branch_pos, commit_pos = pr.to_commit_pos)`.
Conceptually: the corner where the PR arc starts curving from the
source branch toward the target branch's lane. Tracks the merge
target row, so when the target branch progresses past the source tip
the pill follows. The signed two-axis theme offsets
(`pull_request_pill_offset_*`) further nudge the anchor; the per-
orientation defaults live in `gitsvg/theme/_resolve.py`.

Where the pill rect sits relative to that world point comes from the
box anchor resolved by `gitsvg/render/_anchor_resolution.py`. The
PR pill is always centred on the world point (`(0.5, 0.5)`) — its
offset lands away from the start-side margin concern the branch
pill addresses, so the edge-anchoring story doesn't apply. Text is
always centred inside the pill rect.

Width is approximated from the text length using a per-character pixel
estimate; no real glyph measurement.
"""

import drawsvg as draw

from gitsvg.layout import LayoutPullRequest
from gitsvg.render._anchor_resolution import resolve_pr_pill_anchor, rotated_target
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import offset_position
from gitsvg.render._label_widths import pill_width
from gitsvg.theme import Theme


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
        anchor_commit_pos=pr.to_commit_pos,
        branch_axis_offset_in_lanes=theme.pull_request_pill_offset_branch_axis_in_lanes,
        commit_axis_offset_in_rows=theme.pull_request_pill_offset_commit_axis_in_rows,
        canvas=canvas,
    )

    width = pill_width(pr.title, theme)
    height = theme.branch_label_font_size + theme.pill_padding_y
    corner = theme.pill_corner_radius

    box_u, box_v = resolve_pr_pill_anchor(canvas.orientation)
    rect_left = x - box_u * width
    rect_top = y - box_v * height
    text_x = rect_left + width / 2
    text_y = rect_top + height / 2

    target = rotated_target(d, theme.pull_request_label_angle, x, y)
    target.append(
        draw.Rectangle(
            rect_left,
            rect_top,
            width,
            height,
            rx=corner,
            ry=corner,
            fill=color,
            opacity=theme.branch_label_bg_opacity,
        )
    )
    target.append(
        draw.Text(
            pr.title,
            theme.branch_label_font_size,
            text_x,
            text_y,
            text_anchor="middle",
            dominant_baseline="middle",
            fill="white",
            font_family=theme.label_font_family,
            font_weight="500",
        )
    )
