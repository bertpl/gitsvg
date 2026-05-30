"""Connector primitive — the L-shaped arc for branch-off, merge, and
pull-request connectors.

A connector joins a **trunk point** (where it tees laterally into an
ongoing branch) and a **branch point** (where it aligns with a branch's
own start or tip) on two different lanes. It draws two straight legs
joined by a single 90° quarter-arc corner: the lateral leg runs along
the trunk point's row, the tangent leg along the branch point's lane,
and the elbow sits at the branch lane / trunk row.

Which side the branch point falls on — its commit-axis index relative to
the trunk point — gives the connector its appearance:

- **branch point above the trunk** (higher commit-axis index): a
  branch-off. The lateral leg leaves the parent commit first, then the
  tangent leg rises into the new branch.
- **branch point at or below the trunk**: a merge. The tangent leg rises
  out of the merged-in tip first, then the lateral leg tees into the
  merge commit.

These two are mirror images across the commit axis; the draw order and
corner geometry are derived from the two points. In horizontal
orientations (`lr`, `rl`) the branch axis is screen-vertical, so the
on-screen direction of "first leg" flips while the layout-side meaning
is unchanged.

The corner radius is the smaller of `theme.arc_corner_radius` and the
two segment lengths — the corner stays a true quarter circle even when
the endpoints are very close.
"""

import drawsvg as draw

from gitsvg.layout import GridSlot
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
    trunk_point: GridSlot,
    branch_point: GridSlot,
    canvas: RenderCanvas,
    theme: RendererSettings,
    color: str,
    stroke_dasharray: str | None = None,
) -> None:
    """Append an L-shaped connector between a trunk point and a branch point.

    Args:
        d: The drawing to append to.
        trunk_point: The lateral-leg end — where the connector tees into
            the ongoing branch.
        branch_point: The tangent-leg end — a branch's own start or tip.
        canvas: Effective canvas spec, used for the geometry transform.
        theme: Resolved theme; supplies corner radius and stroke width.
        color: Stroke colour for the connector (resolved upstream).
        stroke_dasharray: Optional SVG `stroke-dasharray` value (e.g.
            `"6,4"`). When set, the whole connector is rendered with that
            dash pattern; pull-request connectors pass one to stand apart
            from a real merge.
    """
    # Derive the BT-canonical (from, to, first-leg) triple from the two
    # role-labelled points. A branch point above the trunk (higher commit-
    # axis index) is a branch-off: start at the trunk, run the branch-axis
    # leg first. A branch point at or below the trunk is a merge: start at
    # the branch point, run the commit-axis leg first. Both reproduce the
    # exact path the earlier kind-tagged construction emitted.
    if branch_point.commit_pos > trunk_point.commit_pos:
        from_branch_pos, from_commit_pos = trunk_point.branch_pos, trunk_point.commit_pos
        to_branch_pos, to_commit_pos = branch_point.branch_pos, branch_point.commit_pos
        vertical_first = False
    else:
        from_branch_pos, from_commit_pos = branch_point.branch_pos, branch_point.commit_pos
        to_branch_pos, to_commit_pos = trunk_point.branch_pos, trunk_point.commit_pos
        vertical_first = True

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
