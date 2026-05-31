"""Draw a single branch line — screen direction follows orientation."""

import drawsvg as draw

from gitsvg.layout import LayoutBranch
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import branch_line_endpoints
from gitsvg.render._renderer_settings import RendererSettings


def draw_branch_line(
    d: draw.Drawing, branch: LayoutBranch, color: str, canvas: RenderCanvas, theme: RendererSettings
) -> None:
    """Append a branch's line to the drawing — one straight run per lane segment.

    Each segment spans from its `start` (oldest end) to its `end` (newest
    end) on its own lane. A zero-length segment (`start == end`) is
    skipped: the line would collapse to an invisible zero-length path, so
    emission is suppressed to keep the output free of degenerate elements
    — this also covers an empty branch (a single zero-length segment),
    whose name pill is still drawn beside it. The connectors bridging two
    adjacent segments (lane changes) are emitted separately as arcs.
    Screen direction (vertical vs horizontal) is decided by the geometry
    helper based on `theme.orientation`.
    """
    for segment in branch.segments:
        if segment.start == segment.end:
            continue
        (x_start, y_start), (x_end, y_end) = branch_line_endpoints(segment.lane, segment.start, segment.end, canvas)
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
