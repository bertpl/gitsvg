"""Connector style builders — per-style path geometry, the shared geometry derivation, and the style registry.

A connector joins a trunk point and a branch point on two lanes (see
`arc.py` for the role semantics). `theme.branch_line_style` selects how
the two points are connected:

- `rounded` — two straight legs joined by a single quarter-arc corner
  (the default).
- `straight` — a direct line between the two points (no arc).
- `bezier` — a single flowing cubic curve: both control points coincident
  on the branch point's lane, so it joins that branch's line flush and
  sweeps across to the trunk, with no flat perpendicular leg.
- `double_rounded` — a stepped connector: leave the trunk parallel to its
  lane, two quarter-arcs around an orthogonal crossing one radius from the
  trunk, then a parallel run to the branch.
- `double_bezier` — a smooth cubic-Bézier S, tangent to the commit axis at
  both ends.

Each style is a `_build_<style>(path, geometry)` function that owns its
whole path, opening `M` included. `_connector_geometry` derives the shared
pixel-space `_ConnectorGeometry` once; styles that use the corner radius
clamp the raw `corner_radius` to what their own geometry can fit (the
generic `>= 0` validation lives on the `theme:` op). `_CONNECTOR_BUILDERS`
maps each `BranchLineStyle` to its builder; adding a style is a localized
change: a new enum member, a new `_build_*`, and a new registry entry.
"""

from collections.abc import Callable
from dataclasses import dataclass

import drawsvg as draw

from gitsvg._shared.value_types import BranchLineStyle
from gitsvg.layout import GridSlot
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import grid_to_pixel
from gitsvg.render._renderer_settings import RendererSettings

# Sub-pixel tolerance below which a connector segment degenerates (collapses
# to a straight line). Pure numerical-precision guard; never scales.
_ARC_DEGENERATE_TOLERANCE_PX = 0.5  # axis-symmetric (perceptual)

# `double_bezier` tangent strength: cubic control-point handle length along
# the commit axis, as a fraction of the connector's commit-axis span. 0.5
# places the handles at the midpoint (a gentle S); 1.0 reaches the opposite
# endpoint's row (parallel to the lanes longest, but starts to over-curve).
# 0.75 is the tuned sweet spot.
_DOUBLE_BEZIER_TANGENT_STRENGTH = 0.75  # axis-symmetric (perceptual)

# `bezier` hug strength: how far along the branch point's lane (as a
# fraction of the commit-axis span, measured toward the trunk) the single
# shared control point sits. Higher hugs that lane longer before sweeping
# across to the trunk; lower spreads the sweep into a more evenly diagonal
# line. Tuned by eye against `rounded`.
_BEZIER_HUG_STRENGTH = 0.75  # axis-symmetric (perceptual)


@dataclass(frozen=True, slots=True)
class _ConnectorGeometry:
    """Pixel-space geometry of one connector, derived once and shared by the style builders.

    Attributes:
        x1: Source pixel x (the BT-canonical from-point).
        y1: Source pixel y.
        x2: Target pixel x (the to-point).
        y2: Target pixel y.
        dx: Branch-axis corner direction from source to target (+1 / -1).
        dy: Commit-axis corner direction from source to target (+1 / -1; SVG y-down).
        corner_radius: Raw configured corner radius (px); each style clamps it
            to what its own geometry can fit.
        screen_y_first: `rounded` draws the screen-y leg first when True.
        commit_axis_vertical: True in vertical orientations (`bt` / `tb`),
            where the commit axis runs screen-vertical.
        trunk_is_start: True when the source point is the trunk (branch-off);
            False when the source is the branch and the target is the trunk
            (merge / pull request). Lets `double_rounded` put its crossing
            near the trunk.
    """

    x1: float
    y1: float
    x2: float
    y2: float
    dx: int
    dy: int
    corner_radius: float
    screen_y_first: bool
    commit_axis_vertical: bool
    trunk_is_start: bool


def _connector_geometry(
    trunk_point: GridSlot, branch_point: GridSlot, canvas: RenderCanvas, theme: RendererSettings
) -> _ConnectorGeometry:
    """Derive the shared pixel-space geometry for one connector.

    Resolves the two role-labeled grid points to the BT-canonical (source,
    target, leg-order) — a branch point above the trunk is a branch-off
    (`trunk_is_start`), at or below is a merge — then maps to pixels and the
    active orientation. See `arc.py` for the role semantics.

    Args:
        trunk_point: The endpoint on the ongoing branch.
        branch_point: The endpoint on a branch's own start or tip.
        canvas: Effective canvas spec for the grid → pixel transform.
        theme: Resolved theme; supplies the raw corner radius.

    Returns:
        The `_ConnectorGeometry` every style builder reads.
    """
    trunk_is_start = branch_point.commit_pos > trunk_point.commit_pos
    if trunk_is_start:
        from_branch_pos, from_commit_pos = trunk_point.branch_pos, trunk_point.commit_pos
        to_branch_pos, to_commit_pos = branch_point.branch_pos, branch_point.commit_pos
        vertical_first = False
    else:
        from_branch_pos, from_commit_pos = branch_point.branch_pos, branch_point.commit_pos
        to_branch_pos, to_commit_pos = trunk_point.branch_pos, trunk_point.commit_pos
        vertical_first = True

    x1, y1 = grid_to_pixel(from_branch_pos, from_commit_pos, canvas)
    x2, y2 = grid_to_pixel(to_branch_pos, to_commit_pos, canvas)

    commit_axis_vertical = canvas.orientation.is_vertical
    screen_y_first = vertical_first if commit_axis_vertical else not vertical_first

    dx = 1 if x2 > x1 else -1
    dy = 1 if y2 > y1 else -1  # SVG y-down: positive = down the screen

    return _ConnectorGeometry(
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        dx=dx,
        dy=dy,
        corner_radius=theme.arc_corner_radius,
        screen_y_first=screen_y_first,
        commit_axis_vertical=commit_axis_vertical,
        trunk_is_start=trunk_is_start,
    )


# ==================================================================================================
#  Style builders — each owns its full path (opening M included)
# ==================================================================================================
def _build_rounded(path: draw.Path, g: _ConnectorGeometry) -> None:
    """Two straight legs joined by a single quarter-arc corner.

    The corner radius clamps to either leg so it stays a true quarter
    circle. Degenerate (same row or column) collapses to a straight
    segment. This reproduces the prior-version connector exactly, so default
    output stays byte-identical.
    """
    path.M(g.x1, g.y1)
    r = min(g.corner_radius, abs(g.x2 - g.x1), abs(g.y2 - g.y1))

    if abs(g.y2 - g.y1) < _ARC_DEGENERATE_TOLERANCE_PX:
        path.L(g.x2, g.y1)
        return
    if abs(g.x2 - g.x1) < _ARC_DEGENERATE_TOLERANCE_PX:
        path.L(g.x1, g.y2)
        return

    if g.screen_y_first:
        path.L(g.x1, g.y2 - g.dy * r)
        sweep = 1 if (g.dx > 0) != (g.dy > 0) else 0
        path.A(r, r, 0, 0, sweep, g.x1 + g.dx * r, g.y2)
        if abs(g.x2 - (g.x1 + g.dx * r)) > _ARC_DEGENERATE_TOLERANCE_PX:
            path.L(g.x2, g.y2)
    else:
        path.L(g.x2 - g.dx * r, g.y1)
        sweep = 0 if (g.dx > 0) != (g.dy > 0) else 1
        path.A(r, r, 0, 0, sweep, g.x2, g.y1 + g.dy * r)
        if abs(g.y2 - (g.y1 + g.dy * r)) > _ARC_DEGENERATE_TOLERANCE_PX:
            path.L(g.x2, g.y2)


def _build_straight(path: draw.Path, g: _ConnectorGeometry) -> None:
    """A direct line from the source point to the target point."""
    path.M(g.x1, g.y1)
    path.L(g.x2, g.y2)


def _build_bezier(path: draw.Path, g: _ConnectorGeometry) -> None:
    """A single flowing cubic curve that hugs the branch point's lane, then sweeps to the trunk.

    Both control points are coincident at one point on the **branch
    point's** lane (a branch's own start / tip), `_BEZIER_HUG_STRENGTH` of
    the commit-axis span toward the trunk. The tangent at the branch point
    is therefore along that branch's lane, so the curve joins the branch
    line flush — the new branch rises out of a branch-off, the feature line
    descends into a merge — while the coincident control points concentrate
    the cross-lane sweep toward the trunk, leaving no flat perpendicular
    leg. Which endpoint is the branch point flips with `trunk_is_start`
    (branch-off vs merge / PR). Degenerate (same row or column) collapses to
    a straight segment.
    """
    path.M(g.x1, g.y1)
    if abs(g.y2 - g.y1) < _ARC_DEGENERATE_TOLERANCE_PX:
        path.L(g.x2, g.y1)
        return
    if abs(g.x2 - g.x1) < _ARC_DEGENERATE_TOLERANCE_PX:
        path.L(g.x1, g.y2)
        return

    # `trunk_is_start` ⇒ branch-off (branch point is the to-point); else the
    # branch point is the from-point (merge / PR). The shared control point
    # sits on the branch point's lane, `s` of the way toward the trunk.
    s = _BEZIER_HUG_STRENGTH
    bx, by, tx, ty = (g.x2, g.y2, g.x1, g.y1) if g.trunk_is_start else (g.x1, g.y1, g.x2, g.y2)
    if g.commit_axis_vertical:
        cx, cy = bx, by + s * (ty - by)
    else:
        cx, cy = bx + s * (tx - bx), by
    path.C(cx, cy, cx, cy, g.x2, g.y2)


def _build_double_bezier(path: draw.Path, g: _ConnectorGeometry) -> None:
    """A smooth cubic-Bézier S, tangent to the commit axis at both ends.

    The control points sit on the commit-axis line through each endpoint,
    `_DOUBLE_BEZIER_TANGENT_STRENGTH` of the commit-axis span away — so the
    curve leaves and arrives parallel to the branch lines. Degenerate (same
    row or column) collapses to a straight segment.
    """
    path.M(g.x1, g.y1)
    if abs(g.y2 - g.y1) < _ARC_DEGENERATE_TOLERANCE_PX:
        path.L(g.x2, g.y1)
        return
    if abs(g.x2 - g.x1) < _ARC_DEGENERATE_TOLERANCE_PX:
        path.L(g.x1, g.y2)
        return

    s = _DOUBLE_BEZIER_TANGENT_STRENGTH
    if g.commit_axis_vertical:
        span = g.y2 - g.y1
        path.C(g.x1, g.y1 + s * span, g.x2, g.y2 - s * span, g.x2, g.y2)
    else:
        span = g.x2 - g.x1
        path.C(g.x1 + s * span, g.y1, g.x2 - s * span, g.y2, g.x2, g.y2)


def _step_radius(g: _ConnectorGeometry) -> float:
    """Corner radius for a stepped connector — clamped so both the cross leg and each parallel leg stay ≥ 0.

    Clamps `corner_radius` to half the branch-axis span and half the
    commit-axis span (so `≤ ½` the commit span for a one-row connector).
    """
    return min(g.corner_radius, abs(g.x2 - g.x1) / 2, abs(g.y2 - g.y1) / 2)


def _stepped_path(path: draw.Path, g: _ConnectorGeometry, *, lead: float) -> None:
    """Draw a stepped connector — parallel legs joined by two quarter-arcs around an orthogonal crossing.

    Shared core of the rounded-family stepped shapes. `lead` is the
    straight parallel leg run from the trunk *before* the first arc; the
    crossing then sits `lead + r` along the commit axis from the trunk:

    - `lead = 0` ⇒ crossing one radius from the trunk, the long parallel
      run on the branch side (the asymmetric `double_rounded` tee).
    - `lead = span/2 − r` ⇒ crossing centered between the two rows, with
      equal straight legs each side (the symmetric lane-change).

    Drawn from the trunk; the branch point is the opposite endpoint
    (`trunk_is_start` selects which). Degenerate (same row or column)
    collapses to a straight segment.

    Args:
        path: The path to draw into (this opens it with `M`).
        g: The connector geometry.
        lead: Commit-axis length of the straight leg before the first arc.
    """
    tx, ty, bx, by = (g.x1, g.y1, g.x2, g.y2) if g.trunk_is_start else (g.x2, g.y2, g.x1, g.y1)
    path.M(tx, ty)
    if abs(bx - tx) < _ARC_DEGENERATE_TOLERANCE_PX or abs(by - ty) < _ARC_DEGENERATE_TOLERANCE_PX:
        path.L(bx, by)
        return

    sx = 1 if bx > tx else -1
    sy = 1 if by > ty else -1
    r = _step_radius(g)

    if g.commit_axis_vertical:
        # Parallel = screen-y, orthogonal = screen-x; crossing `lead + r` up.
        if lead:
            path.L(tx, ty + sy * lead)
        y0 = ty + sy * lead
        path.A(r, r, 0, 0, 1 if sx * sy < 0 else 0, tx + sx * r, y0 + sy * r)
        path.L(bx - sx * r, y0 + sy * r)
        path.A(r, r, 0, 0, 1 if sx * sy > 0 else 0, bx, y0 + 2 * sy * r)
        path.L(bx, by)
    else:
        # Parallel = screen-x, orthogonal = screen-y; crossing `lead + r` over.
        if lead:
            path.L(tx + sx * lead, ty)
        x0 = tx + sx * lead
        path.A(r, r, 0, 0, 1 if sx * sy > 0 else 0, x0 + sx * r, ty + sy * r)
        path.L(x0 + sx * r, by - sy * r)
        path.A(r, r, 0, 0, 1 if sx * sy < 0 else 0, x0 + 2 * sx * r, by)
        path.L(bx, by)


def _build_double_rounded(path: draw.Path, g: _ConnectorGeometry) -> None:
    """A stepped connector with its orthogonal crossing one radius from the trunk.

    Leaves the trunk parallel to its lane, arcs to orthogonal, crosses the
    lane gap one radius from the trunk, arcs back to parallel, then runs
    parallel the rest of the way to the branch. `lead = 0` case of
    `_stepped_path`.
    """
    _stepped_path(path, g, lead=0.0)


_CONNECTOR_BUILDERS: dict[BranchLineStyle, Callable[[draw.Path, _ConnectorGeometry], None]] = {
    BranchLineStyle.ROUNDED: _build_rounded,
    BranchLineStyle.STRAIGHT: _build_straight,
    BranchLineStyle.BEZIER: _build_bezier,
    BranchLineStyle.DOUBLE_ROUNDED: _build_double_rounded,
    BranchLineStyle.DOUBLE_BEZIER: _build_double_bezier,
}


# ==================================================================================================
#  Lane-change builders — a branch's own line shifting lanes (both endpoints on that branch)
# ==================================================================================================
# A lane-change connector has both endpoints on the *same* migrating branch,
# one row apart, so it reads as "this branch shifted over" rather than a tee.
# It is symmetric — no trunk / branch role — so each style draws its
# both-ends-parallel double-bend: the curved styles (`bezier` /
# `double_bezier`) reuse the already-symmetric `_build_double_bezier` S;
# `straight` keeps its direct diagonal; the rounded family gets a centered
# stepped shape (crossing in the middle, equal straight legs each side),
# distinct from `double_rounded`'s trunk-biased tee.
def _build_lane_change_stepped(path: draw.Path, g: _ConnectorGeometry) -> None:
    """A symmetric stepped lane-change — crossing centered between the two rows, equal straight legs each side.

    The `lead = span/2 − r` case of `_stepped_path`, where `span` is the
    commit-axis distance between the endpoints. Used for `rounded` and
    `double_rounded` lane changes (their tees differ, but a lane change
    reads the same for both).
    """
    span = abs(g.y2 - g.y1) if g.commit_axis_vertical else abs(g.x2 - g.x1)
    _stepped_path(path, g, lead=span / 2 - _step_radius(g))


_LANE_CHANGE_BUILDERS: dict[BranchLineStyle, Callable[[draw.Path, _ConnectorGeometry], None]] = {
    BranchLineStyle.STRAIGHT: _build_straight,
    BranchLineStyle.ROUNDED: _build_lane_change_stepped,
    BranchLineStyle.DOUBLE_ROUNDED: _build_lane_change_stepped,
    BranchLineStyle.BEZIER: _build_double_bezier,
    BranchLineStyle.DOUBLE_BEZIER: _build_double_bezier,
}
