"""Draw a single dashed branch guide — a faint vertical line behind a lane.

One guide is drawn per occupied branch-axis lane, spanning the full
canvas content area with a small overshoot above and below. Guides
sit at the bottom of the z-order (right above the optional background
rect); everything else draws on top.
"""

import drawsvg as draw

from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import branch_axis_to_x, branch_guide_endpoints
from gitsvg.theme import Theme


def draw_branch_guide(d: draw.Drawing, branch_pos: int, canvas: RenderCanvas, theme: Theme) -> None:
    """Append a dashed vertical guide for a single lane to the drawing."""
    x = branch_axis_to_x(branch_pos, canvas)
    y_top, y_bottom = branch_guide_endpoints(canvas, theme)
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
