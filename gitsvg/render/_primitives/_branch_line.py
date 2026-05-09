"""Draw a single branch line as a vertical line in the branch's lane."""

import drawsvg as draw

from gitsvg.layout import LayoutBranch
from gitsvg.render._constants import BRANCH_LINE_WIDTH
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y


def draw_branch_line(d: draw.Drawing, branch: LayoutBranch, color: str, n_commits: int) -> None:
    """Append a branch line to the drawing.

    The line spans from the branch's `start` (oldest end) to its `end`
    (newest commit on the branch). For an empty branch (`start == end`)
    the line collapses to a point — the branch is effectively invisible
    until labels are drawn (PR6).
    """
    x = branch_axis_to_x(branch.branch_pos)
    y_start = commit_axis_to_y(branch.start, n_commits)
    y_end = commit_axis_to_y(branch.end, n_commits)
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
