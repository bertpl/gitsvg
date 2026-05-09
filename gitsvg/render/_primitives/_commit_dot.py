"""Draw a single commit dot at its layout position."""

import drawsvg as draw

from gitsvg._visual_constants import COMMIT_RADIUS, COMMIT_STROKE_WIDTH, HIGHLIGHT_RADIUS
from gitsvg.layout import LayoutCanvas, LayoutCommit
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y


def draw_commit_dot(d: draw.Drawing, commit: LayoutCommit, color: str, canvas: LayoutCanvas) -> None:
    """Append a commit dot to the drawing.

    Highlighted commits render with `HIGHLIGHT_RADIUS` (40 % bigger
    than `COMMIT_RADIUS`); the bold label is wired separately in the
    label primitive.
    """
    x = branch_axis_to_x(commit.branch_pos, canvas)
    y = commit_axis_to_y(commit.commit_pos, canvas)
    radius = HIGHLIGHT_RADIUS if commit.highlight else COMMIT_RADIUS
    d.append(
        draw.Circle(
            x,
            y,
            radius,
            fill=color,
            stroke="white",
            stroke_width=COMMIT_STROKE_WIDTH,
        )
    )
