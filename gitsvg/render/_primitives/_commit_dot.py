"""Draw a single commit dot at its layout position."""

import drawsvg as draw

from gitsvg.layout import LayoutCommit
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import grid_to_pixel
from gitsvg.theme import Theme


def draw_commit_dot(d: draw.Drawing, commit: LayoutCommit, color: str, canvas: RenderCanvas, theme: Theme) -> None:
    """Append a commit dot to the drawing.

    Highlighted commits render with `theme.highlight_radius` (40 %
    bigger than `theme.commit_radius`); the bold label is wired
    separately in the label primitive.
    """
    x, y = grid_to_pixel(commit.branch_pos, commit.commit_pos, canvas)
    radius = theme.highlight_radius if commit.highlight else theme.commit_radius
    d.append(
        draw.Circle(
            x,
            y,
            radius,
            fill=color,
            stroke="white",
            stroke_width=theme.commit_stroke_width,
        )
    )
