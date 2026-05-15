"""Draw a branch-name pill at the branch's start point.

The pill is a filled rounded rectangle in the branch's colour with the
branch name in white text, positioned at the signed two-axis offset
declared on the theme — `branch_name_pill_offset_commit_axis_in_rows`
and `branch_name_pill_offset_branch_axis_in_lanes`. The resolver in
`gitsvg/theme/_resolve.py` picks per-orientation defaults: vertical
orientations route the offset along the commit axis (pill below the
start in BT, above in TB); horizontal orientations route it along the
commit axis with `-0.75 × commit_spacing` (pill alongside the branch
line, before the start commit in `lr` / after in `rl`).

In horizontal orientations the pill rect is anchored on the **edge
nearest the start commit** instead of being centred on the offset
point — so the offset becomes a minimum gap between the start commit
and the pill, regardless of pill width. Long branch names extend
further into the margin without ever overlapping the start commit
dot. The text itself is always centred inside the pill rect (via
``text_anchor="middle"`` at the rect's centre), independent of the
rect's anchoring strategy.
"""

import drawsvg as draw

from gitsvg.layout import LayoutBranch
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import offset_position
from gitsvg.render._label_widths import pill_width
from gitsvg.theme import Theme


def draw_branch_pill(d: draw.Drawing, branch: LayoutBranch, color: str, canvas: RenderCanvas, theme: Theme) -> None:
    """Append a branch-name pill (background rectangle + text) to the drawing."""
    x, y = offset_position(
        anchor_branch_pos=branch.branch_pos,
        anchor_commit_pos=branch.start,
        branch_axis_offset_in_lanes=theme.branch_name_pill_offset_branch_axis_in_lanes,
        commit_axis_offset_in_rows=theme.branch_name_pill_offset_commit_axis_in_rows,
        canvas=canvas,
    )

    width = pill_width(branch.name, theme)
    height = theme.branch_label_font_size + theme.pill_padding_y
    corner = theme.pill_corner_radius

    # Rect anchoring (orientation-dependent) and text positioning
    # (always centred in the rect) are decoupled:
    # - BT/TB: rect centred on (x, y).
    # - LR: rect's right edge at (x, y); rect extends leftward so a
    #   long pill never overlaps the start commit to the right.
    # - RL: mirror of LR — left edge at (x, y); extends rightward.
    # In every orientation the text sits at the rect's centre via
    # `text_anchor="middle"`, so the visible text stays centred inside
    # the pill regardless of any drift between predicted and actual
    # rendered text width.
    if canvas.orientation == "lr":
        rect_left = x - width
    elif canvas.orientation == "rl":
        rect_left = x
    else:
        rect_left = x - width / 2
    text_x = rect_left + width / 2

    d.append(
        draw.Rectangle(
            rect_left,
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
            branch.name,
            theme.branch_label_font_size,
            text_x,
            y,
            text_anchor="middle",
            dominant_baseline="middle",
            fill="white",
            font_family=theme.label_font_family,
            font_weight="500",
        )
    )
