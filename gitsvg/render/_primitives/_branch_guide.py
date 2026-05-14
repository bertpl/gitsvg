"""Draw a single dashed branch guide — a faint vertical line behind a lane.

One guide is drawn per occupied branch-axis lane, spanning the full
canvas content area with a small overshoot above and below. Guides
sit at the bottom of the z-order (right above the optional background
rect); everything else draws on top.
"""

import drawsvg as draw

from gitsvg._theme import Theme
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import branch_axis_to_x

_OVERSHOOT_PX = 10  # axis-bound: commit-axis (applied symmetrically at both ends)


def draw_branch_guide(d: draw.Drawing, branch_pos: int, canvas: RenderCanvas, theme: Theme) -> None:
    """Append a dashed vertical guide for a single lane to the drawing."""
    x = branch_axis_to_x(branch_pos, canvas)
    y_top = canvas.margin_commit_axis_upper - _OVERSHOOT_PX
    y_bottom = canvas.height - canvas.margin_commit_axis_lower + _OVERSHOOT_PX
    d.append(
        draw.Line(
            x,
            y_top,
            x,
            y_bottom,
            stroke=theme.branch_guide_color,
            stroke_width=theme.branch_guide_width,
            stroke_dasharray=theme.branch_guide_dash,
        )
    )
