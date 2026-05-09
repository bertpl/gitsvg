"""Draw a single dashed branch guide — a faint vertical line behind a lane.

One guide is drawn per occupied branch-axis lane, spanning the full
canvas content area with a small overshoot above and below. Guides
sit at the bottom of the z-order; everything else draws on top.
"""

import drawsvg as draw

from gitsvg._visual_constants import (
    BRANCH_GUIDE_COLOR,
    BRANCH_GUIDE_DASH,
    BRANCH_GUIDE_WIDTH,
    MARGIN_COMMIT_AXIS_LOWER,
    MARGIN_COMMIT_AXIS_UPPER,
)
from gitsvg.render._geometry import branch_axis_to_x

_OVERSHOOT_PX = 10


def draw_branch_guide(d: draw.Drawing, branch_pos: int, canvas_height: float) -> None:
    """Append a dashed vertical guide for a single lane to the drawing."""
    x = branch_axis_to_x(branch_pos)
    y_top = MARGIN_COMMIT_AXIS_UPPER - _OVERSHOOT_PX
    y_bottom = canvas_height - MARGIN_COMMIT_AXIS_LOWER + _OVERSHOOT_PX
    d.append(
        draw.Line(
            x,
            y_top,
            x,
            y_bottom,
            stroke=BRANCH_GUIDE_COLOR,
            stroke_width=BRANCH_GUIDE_WIDTH,
            stroke_dasharray=BRANCH_GUIDE_DASH,
        )
    )
