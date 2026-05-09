"""Quarter-arc primitive — used for branch-off and merge connectors.

The arc connects two points on different branch-axis lanes at different
commit-axis positions, with a single 90° corner. Two modes:

- **Horizontal-first** (`vertical_first=False`, the default): straight
  segment along the branch axis from the source point, then a quarter
  arc, then a straight segment along the commit axis to the target.
  Used for **branch-off** connectors.

- **Vertical-first** (`vertical_first=True`): straight segment along
  the commit axis from the source point, then a quarter arc, then a
  straight segment along the branch axis to the target. Used for
  **merge** connectors.

The arc's corner radius is the smaller of `ARC_CORNER_RADIUS` and the
two segment lengths — the corner stays a true quarter circle even when
the two endpoints are very close.
"""

import drawsvg as draw

from gitsvg._visual_constants import ARC_CORNER_RADIUS, BRANCH_LINE_WIDTH
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y


def draw_arc(
    d: draw.Drawing,
    *,
    from_branch_pos: int,
    from_commit_pos: int,
    to_branch_pos: int,
    to_commit_pos: int,
    n_commits: int,
    color: str,
    vertical_first: bool,
) -> None:
    """Append a quarter-arc connector to the drawing.

    Args:
        d: The drawing to append to.
        from_branch_pos: Source point's branch-axis index.
        from_commit_pos: Source point's commit-axis index.
        to_branch_pos: Target point's branch-axis index.
        to_commit_pos: Target point's commit-axis index.
        n_commits: Total commit-axis slots (passed through to the
            geometry transform).
        color: Stroke colour for the arc.
        vertical_first: When True, the arc starts with a vertical
            segment (used for merge connectors). When False, it starts
            horizontal (used for branch-off connectors).
    """
    x1 = branch_axis_to_x(from_branch_pos)
    y1 = commit_axis_to_y(from_commit_pos, n_commits)
    x2 = branch_axis_to_x(to_branch_pos)
    y2 = commit_axis_to_y(to_commit_pos, n_commits)

    p = draw.Path(
        stroke=color,
        stroke_width=BRANCH_LINE_WIDTH,
        fill="none",
        stroke_linecap="round",
    )
    p.M(x1, y1)

    # Same row → degenerate to a straight horizontal segment.
    if abs(y2 - y1) < 0.5:
        p.L(x2, y1)
        d.append(p)
        return

    dx = 1 if x2 > x1 else -1
    dy = -1 if y2 < y1 else 1  # SVG y-down: negative = up the screen
    r = min(ARC_CORNER_RADIUS, abs(x2 - x1), abs(y2 - y1))

    if vertical_first:
        # Vertical segment from source toward the target's row.
        p.L(x1, y2 - dy * r)
        # Quarter-circle arc turning horizontal. Sweep flips compared to
        # horizontal-first because the curve bends the other way.
        sweep = 1 if (dx > 0) != (dy > 0) else 0
        p.A(r, r, 0, 0, sweep, x1 + dx * r, y2)
        # Horizontal segment to target.
        if abs(x2 - (x1 + dx * r)) > 0.5:
            p.L(x2, y2)
    else:
        # Horizontal segment from source toward the target's lane.
        p.L(x2 - dx * r, y1)
        # Quarter-circle arc turning vertical.
        sweep = 0 if (dx > 0) != (dy > 0) else 1
        p.A(r, r, 0, 0, sweep, x2, y1 + dy * r)
        # Vertical segment to target.
        if abs(y2 - (y1 + dy * r)) > 0.5:
            p.L(x2, y2)

    d.append(p)
