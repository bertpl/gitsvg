"""Draw a branch-name pill at the branch's start point.

The pill is a filled rounded rectangle in the branch's colour with the
branch name in white text, positioned at the signed two-axis offset
declared on the theme — `branch_name_pill_offset_commit_axis_in_rows`
(default `-0.5`, putting the pill below the branch's start row in BT)
and `branch_name_pill_offset_branch_axis_in_lanes` (default `0`,
keeping the pill centred on the branch's lane).

Width is approximated from the text length using a per-character pixel
estimate; no real glyph measurement.
"""

import drawsvg as draw

from gitsvg._theme import Theme
from gitsvg.layout import LayoutBranch
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import offset_position
from gitsvg.render._metrics import _CHAR_WIDTH_FACTOR_NORMAL


def draw_branch_pill(d: draw.Drawing, branch: LayoutBranch, color: str, canvas: RenderCanvas, theme: Theme) -> None:
    """Append a branch-name pill (background rectangle + text) to the drawing."""
    x, y = offset_position(
        anchor_branch_pos=branch.branch_pos,
        anchor_commit_pos=branch.start,
        branch_axis_offset_in_lanes=theme.branch_name_pill_offset_branch_axis_in_lanes,
        commit_axis_offset_in_rows=theme.branch_name_pill_offset_commit_axis_in_rows,
        canvas=canvas,
    )

    width = len(branch.name) * theme.branch_label_font_size * _CHAR_WIDTH_FACTOR_NORMAL + theme.pill_padding_x
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
            branch.name,
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
