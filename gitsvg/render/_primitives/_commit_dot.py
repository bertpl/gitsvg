"""Draw a single commit dot at its layout position."""

import drawsvg as draw

from gitsvg._visual_constants import COMMIT_RADIUS, COMMIT_STROKE_WIDTH
from gitsvg.layout import LayoutCommit
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y


def draw_commit_dot(d: draw.Drawing, commit: LayoutCommit, color: str, n_commits: int) -> None:
    """Append a commit dot to the drawing.

    PR4 always uses `COMMIT_RADIUS`. The highlight visual (enlarged
    dot + bold label) lands in PR6.
    """
    x = branch_axis_to_x(commit.branch_pos)
    y = commit_axis_to_y(commit.commit_pos, n_commits)
    d.append(
        draw.Circle(
            x,
            y,
            COMMIT_RADIUS,
            fill=color,
            stroke="white",
            stroke_width=COMMIT_STROKE_WIDTH,
        )
    )
