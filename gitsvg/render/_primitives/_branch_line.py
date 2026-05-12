"""Draw a single branch line as a vertical line in the branch's lane."""

import drawsvg as draw

from gitsvg.layout import LayoutBranch
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y
from gitsvg.render._theme import Theme


def draw_branch_line(d: draw.Drawing, branch: LayoutBranch, color: str, canvas: RenderCanvas, theme: Theme) -> None:
    """Append a branch line to the drawing.

    The line spans from the branch's `start` (oldest end) to its `end`
    (newest commit on the branch). Skipped entirely for empty branches
    (`start == end`): the line would collapse to an invisible
    zero-length path, so emission is suppressed to keep the output
    free of degenerate elements. The branch's name pill is still
    drawn beside it.
    """
    if branch.start == branch.end:
        return
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
            stroke_width=theme.branch_line_width,
            stroke_linecap="round",
        )
    )
