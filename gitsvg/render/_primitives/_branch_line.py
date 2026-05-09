"""Draw a single branch line as a vertical line in the branch's lane."""

import drawsvg as draw

from gitsvg._visual_constants import BRANCH_LINE_WIDTH
from gitsvg.layout import LayoutBranch, LayoutCanvas
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y


def draw_branch_line(d: draw.Drawing, branch: LayoutBranch, color: str, canvas: LayoutCanvas) -> None:
    """Append a branch line to the drawing.

    The line spans from the branch's `start` (oldest end) to its `end`
    (newest commit on the branch). For an empty branch (`start == end`)
    the line collapses to a point — the branch is effectively invisible
    until its name pill is drawn beside it.
    """
    x = branch_axis_to_x(branch.branch_pos, canvas)
    y_start = commit_axis_to_y(branch.start, canvas)
    y_end = commit_axis_to_y(branch.end, canvas)
    d.append(
        draw.Line(
            x,
            y_start,
            x,
            y_end,
            stroke=color,
            stroke_width=BRANCH_LINE_WIDTH,
            stroke_linecap="round",
        )
    )
