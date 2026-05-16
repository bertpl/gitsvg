"""Draw a single branch line — screen direction follows orientation."""

import drawsvg as draw

from gitsvg.layout import LayoutBranch
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import branch_line_endpoints
from gitsvg.render._renderer_settings import RendererSettings


def draw_branch_line(
    d: draw.Drawing, branch: LayoutBranch, color: str, canvas: RenderCanvas, theme: RendererSettings
) -> None:
    """Append a branch line to the drawing.

    The line spans from the branch's `start` (oldest end) to its `end`
    (newest commit on the branch). Skipped entirely for empty branches
    (`start == end`): the line would collapse to an invisible
    zero-length path, so emission is suppressed to keep the output
    free of degenerate elements. The branch's name pill is still
    drawn beside it. Screen direction (vertical vs horizontal) is
    decided by the geometry helper based on `theme.orientation`.
    """
    if branch.start == branch.end:
        return
    (x_start, y_start), (x_end, y_end) = branch_line_endpoints(branch.branch_pos, branch.start, branch.end, canvas)
    d.append(
        draw.Line(
            x_start,
            y_start,
            x_end,
            y_end,
            stroke=color,
            stroke_width=theme.branch_line_width,
            stroke_linecap="round",
        )
    )
