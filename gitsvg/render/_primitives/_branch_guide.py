"""Draw a single dashed branch guide — screen direction follows orientation.

One guide is drawn per occupied branch-axis lane, spanning the full
canvas content area with a small overshoot past the margin edges.
Guides sit at the bottom of the z-order (right above the optional
background rect); everything else draws on top.
"""

import drawsvg as draw

from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import branch_guide_endpoints
from gitsvg.theme import Theme


def draw_branch_guide(d: draw.Drawing, branch_pos: int, canvas: RenderCanvas, theme: Theme) -> None:
    """Append a dashed guide for a single lane to the drawing.

    Screen direction (vertical in `bt`/`tb`, horizontal in `lr`/`rl`)
    is decided by the geometry helper based on `theme.orientation`.
    """
    (x1, y1), (x2, y2) = branch_guide_endpoints(branch_pos, canvas, theme)
    d.append(
        draw.Line(
            x1,
            y1,
            x2,
            y2,
            stroke=theme.branch_guide_color,
            stroke_width=theme.branch_guide_width,
            stroke_dasharray=theme.branch_guide_dash,
        )
    )
