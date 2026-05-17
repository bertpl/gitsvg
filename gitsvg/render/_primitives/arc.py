"""Quarter-arc primitive — used for branch-off and merge connectors.

The arc connects two points on different branch-axis lanes at different
commit-axis positions, with a single 90° corner. Two modes (parameter
name is screen-direction in BT-canonical terms; the renderer maps to
the active orientation):

- **Horizontal-first** (`vertical_first=False`): the arc starts with a
  segment along the branch axis (BT: horizontal), then turns to the
  commit axis (BT: vertical). Used for **branch-off** connectors.

- **Vertical-first** (`vertical_first=True`): the arc starts with a
  segment along the commit axis (BT: vertical), then turns to the
  branch axis (BT: horizontal). Used for **merge** connectors.

In horizontal orientations (`lr`, `rl`) the screen-direction of "first
segment" flips because the branch axis becomes vertical on screen, but
the layout-side meaning of "branch-axis-first vs commit-axis-first"
stays the same.

The arc's corner radius is the smaller of `theme.arc_corner_radius`
and the two segment lengths — the corner stays a true quarter circle
even when the two endpoints are very close.
"""

import drawsvg as draw

from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import grid_to_pixel
from gitsvg.render._renderer_settings import RendererSettings
from gitsvg.theme import Orientation

# Sub-pixel tolerance below which arc segments degenerate (collapse to a
# straight line, or skip an emit entirely). Pure numerical-precision guard;
# never scales with anything else.
_ARC_DEGENERATE_TOLERANCE_PX = 0.5  # axis-symmetric (perceptual)


def draw_arc(
    d: draw.Drawing,
    *,
    from_branch_pos: int,
    from_commit_pos: int,
    to_branch_pos: int,
    to_commit_pos: int,
    canvas: RenderCanvas,
    theme: RendererSettings,
    color: str,
    vertical_first: bool,
    stroke_dasharray: str | None = None,
) -> None:
    """Append a quarter-arc connector to the drawing.

    Args:
        d: The drawing to append to.
        from_branch_pos: Source point's branch-axis index.
        from_commit_pos: Source point's commit-axis index.
        to_branch_pos: Target point's branch-axis index.
        to_commit_pos: Target point's commit-axis index.
        canvas: Effective canvas spec, used for the geometry transform.
        theme: Resolved theme; supplies corner radius and stroke width.
        color: Stroke colour for the arc (resolved from the theme upstream).
        vertical_first: BT-canonical screen direction of the first
            segment. `True` = first segment along the commit axis
            (vertical in BT, horizontal in LR/RL). Used for merge
            connectors. `False` = first segment along the branch axis
            (horizontal in BT, vertical in LR/RL). Used for branch-off
            connectors. The renderer maps this layout-side intent to
            the active orientation's screen direction.
        stroke_dasharray: Optional SVG `stroke-dasharray` value (e.g.
            `"6,4"`). When set, the entire arc-and-line is rendered
            with that dash pattern; used by pull-request connectors
            to visually distinguish them from a real merge.
    """
    x1, y1 = grid_to_pixel(from_branch_pos, from_commit_pos, canvas)
    x2, y2 = grid_to_pixel(to_branch_pos, to_commit_pos, canvas)

    # Map the layout-side `vertical_first` (BT-canonical screen direction)
    # to the active orientation's first-segment screen axis. In vertical
    # orientations (`bt`, `tb`) the commit axis is screen-vertical and
    # the branch axis is screen-horizontal; in horizontal orientations
    # (`lr`, `rl`) those swap. So `vertical_first` (= "commit-axis-first
    # in BT terms") becomes `screen_y_first` only in vertical
    # orientations; in horizontal orientations it becomes
    # `screen_x_first`.
    is_vertical_orientation = canvas.orientation in (Orientation.BT, Orientation.TB)
    screen_y_first = vertical_first if is_vertical_orientation else not vertical_first

    path_kwargs: dict = {
        "stroke": color,
        "stroke_width": theme.branch_line_width,
        "fill": "none",
        "stroke_linecap": "round",
    }
    if stroke_dasharray is not None:
        path_kwargs["stroke_dasharray"] = stroke_dasharray

    p = draw.Path(**path_kwargs)
    p.M(x1, y1)

    # Same row OR same column → degenerate to a straight segment along
    # the differing axis.
    if abs(y2 - y1) < _ARC_DEGENERATE_TOLERANCE_PX:
        p.L(x2, y1)
        d.append(p)
        return
    if abs(x2 - x1) < _ARC_DEGENERATE_TOLERANCE_PX:
        p.L(x1, y2)
        d.append(p)
        return

    dx = 1 if x2 > x1 else -1
    dy = 1 if y2 > y1 else -1  # SVG y-down: positive = down the screen
    r = min(theme.arc_corner_radius, abs(x2 - x1), abs(y2 - y1))

    if screen_y_first:
        # First segment along screen-y axis from source toward target row.
        p.L(x1, y2 - dy * r)
        # Quarter-circle arc turning toward x. Sweep depends on the
        # direction quadrant: when dx and dy have the same sign, the
        # corner curves one way; opposite signs curve the other way.
        sweep = 1 if (dx > 0) != (dy > 0) else 0
        p.A(r, r, 0, 0, sweep, x1 + dx * r, y2)
        if abs(x2 - (x1 + dx * r)) > _ARC_DEGENERATE_TOLERANCE_PX:
            p.L(x2, y2)
    else:
        # First segment along screen-x axis from source toward target lane.
        p.L(x2 - dx * r, y1)
        # Quarter-circle arc turning toward y. Sweep flips relative to
        # screen_y_first because the curve bends the other way.
        sweep = 0 if (dx > 0) != (dy > 0) else 1
        p.A(r, r, 0, 0, sweep, x2, y1 + dy * r)
        if abs(y2 - (y1 + dy * r)) > _ARC_DEGENERATE_TOLERANCE_PX:
            p.L(x2, y2)

    d.append(p)
