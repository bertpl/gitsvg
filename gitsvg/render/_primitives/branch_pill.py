"""Draw a branch-name pill at the branch's start point.

The pill is a filled rounded rectangle in the branch's colour with the
branch name in white text. Its world anchor point comes from the
signed two-axis offset declared on the theme
(`branch_name_pill_offset_commit_axis_in_rows` and
`branch_name_pill_offset_branch_axis_in_lanes`); the per-orientation
defaults live in `gitsvg/theme/_resolve.py`.

Where the pill rect sits relative to that world point — centred,
right-edge anchored, left-edge anchored — comes from the box anchor
resolved by `gitsvg/render/_anchor_resolution.py`. Vertical
orientations (`bt`, `tb`) centre the pill (`(0.5, 0.5)`); horizontal
orientations anchor the pill's edge nearest the start commit so the
theme offset becomes a minimum gap and a long branch name extends
further into the start-side margin without crowding the dot. The text
itself is always centred inside the pill rect — pill-internal text
placement is invariant.
"""

import drawsvg as draw

from gitsvg.layout import LayoutBranch
from gitsvg.render._anchor_resolution import rotated_target
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import offset_position
from gitsvg.render._label_widths import pill_width
from gitsvg.render._primitives._pill import draw_pill_box
from gitsvg.render._renderer_settings import RendererSettings


def draw_branch_pill(
    d: draw.Drawing, branch: LayoutBranch, color: str, canvas: RenderCanvas, theme: RendererSettings
) -> None:
    """Append a branch-name pill (background rectangle + text) to the drawing."""
    x, y = offset_position(
        anchor_branch_pos=branch.start_lane,
        anchor_commit_pos=branch.start,
        branch_axis_offset_in_lanes=theme.branch_name_pill_offset_branch_axis_in_lanes,
        commit_axis_offset_in_rows=theme.branch_name_pill_offset_commit_axis_in_rows,
        canvas=canvas,
    )

    width = pill_width(branch.name, theme)
    height = theme.branch_label_font_size + theme.pill_padding_y

    box_u, box_v = theme.branch_pill_anchor
    rect_left = x - box_u * width
    rect_top = y - box_v * height

    target = rotated_target(d, theme.branch_label_angle, x, y)
    draw_pill_box(
        target,
        left=rect_left,
        top=rect_top,
        width=width,
        height=height,
        text=branch.name,
        color=color,
        theme=theme,
    )
