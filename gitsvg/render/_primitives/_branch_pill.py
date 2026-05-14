"""Draw a branch-name pill at the branch's start point.

The pill is a filled rounded rectangle in the branch's colour with the
branch name in white text, positioned `theme.branch_name_pill_offset`
pixels *below* the branch's start point in screen y (= towards the
lower end of the commit axis, where pills sit at the branch's birth).

Width is approximated from the text length using a per-character pixel
estimate; no real glyph measurement.
"""

import drawsvg as draw

from gitsvg._theme import Theme
from gitsvg.layout import LayoutBranch
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import offset_position
from gitsvg.render._metrics import (
    _CHAR_WIDTH_FACTOR_NORMAL,
    _PILL_CORNER_RADIUS,
    _PILL_PADDING_X,
    _PILL_PADDING_Y,
)


def draw_branch_pill(d: draw.Drawing, branch: LayoutBranch, color: str, canvas: RenderCanvas, theme: Theme) -> None:
    """Append a branch-name pill (background rectangle + text) to the drawing."""
    x, y = offset_position(
        anchor_branch_pos=branch.branch_pos,
        anchor_commit_pos=branch.start,
        branch_axis_offset_px=0,
        commit_axis_offset_px=theme.branch_name_pill_offset,
        canvas=canvas,
    )

    width = len(branch.name) * theme.branch_label_font_size * _CHAR_WIDTH_FACTOR_NORMAL + _PILL_PADDING_X
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
