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
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y

_PILL_PADDING_X = 12  # extra width beyond the rendered text
_PILL_PADDING_Y = 8  # extra height beyond the font size
_PILL_CORNER_RADIUS = 4
_CHAR_WIDTH_FACTOR = 0.58  # rough char-width estimate at weight 500


def draw_branch_pill(d: draw.Drawing, branch: LayoutBranch, color: str, canvas: RenderCanvas, theme: Theme) -> None:
    """Append a branch-name pill (background rectangle + text) to the drawing."""
    x = branch_axis_to_x(branch.branch_pos, canvas)
    y = commit_axis_to_y(branch.start, canvas) + theme.branch_name_pill_offset

    width = len(branch.name) * theme.branch_label_font_size * _CHAR_WIDTH_FACTOR + _PILL_PADDING_X
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
