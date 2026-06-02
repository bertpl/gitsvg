"""Connector orchestrator — resolve a connector's geometry and dispatch
to its style builder.

A connector joins a **trunk point** (where it tees into an ongoing
branch — the parent commit for a branch-off, the merge commit for a
merge) and a **branch point** (a branch's own start or tip) on two
different lanes, and is drawn for branch-off, merge, and pull-request
connectors alike.

`draw_arc` is a thin orchestrator: it derives the shared
`_ConnectorGeometry` once (resolving the two role-labeled points to pixel
endpoints and the orientation-mapped leg order), creates the SVG path, and
dispatches to the builder registered for `theme.branch_line_style` in
`_connector_styles` — the builder draws the whole connector (opening `M`
included). The per-style geometry (rounded / straight / bezier /
double_rounded / double_bezier) lives there.

Whether the branch point sits above or below the trunk point (its
commit-axis index) gives a connector its branch-off vs merge appearance —
they are mirror images across the commit axis — and the orientation
mapping handles `lr` / `rl` (where the branch axis is screen-vertical).
"""

import drawsvg as draw

from gitsvg.layout import GridSlot, LayoutArcKind
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._primitives.connector_styles import (
    _CONNECTOR_BUILDERS,
    _LANE_CHANGE_BUILDERS,
    _connector_geometry,
)
from gitsvg.render._renderer_settings import RendererSettings


def draw_arc(
    d: draw.Drawing,
    *,
    trunk_point: GridSlot,
    branch_point: GridSlot,
    canvas: RenderCanvas,
    theme: RendererSettings,
    color: str,
    stroke_dasharray: str | None = None,
    kind: LayoutArcKind | None = None,
) -> None:
    """Append a connector between a trunk point and a branch point.

    Branch-off / merge / pull-request connectors take their shape from
    `theme.branch_line_style` (`rounded` / `straight` / `bezier` /
    `double_rounded` / `double_bezier`), dispatched through the `_connector_styles`
    registry. `rounded` is the default and renders byte-identically to
    prior versions.

    A lane-change connector (`kind=LANE_CHANGE`) — both endpoints on one
    migrating branch — dispatches through the `_LANE_CHANGE_BUILDERS`
    registry instead, so each style draws its own both-ends-parallel
    double-bend (the lane-change idiom) rather than its branch-off / merge
    tee.

    Args:
        d: The drawing to append to.
        trunk_point: The endpoint on the ongoing branch — the parent
            commit for a branch-off, the merge commit for a merge, the
            old-lane tail for a lane-change.
        branch_point: The endpoint on a branch's own line — that branch's
            start (branch-off), tip (merge), or new-lane head
            (lane-change).
        canvas: Effective canvas spec, used for the geometry transform.
        theme: Resolved theme; supplies the connector style, corner
            radius, and stroke width.
        color: Stroke color for the connector (resolved upstream).
        stroke_dasharray: Optional SVG `stroke-dasharray` value (e.g.
            `"6,4"`). When set, the whole connector is rendered with that
            dash pattern; pull-request connectors pass one to stand apart
            from a real merge.
        kind: The connector's role. `LANE_CHANGE` dispatches through
            `_LANE_CHANGE_BUILDERS`; every other value (and `None`, for
            pull requests) dispatches through `_CONNECTOR_BUILDERS`. Both
            key on `theme.branch_line_style`.
    """
    geom = _connector_geometry(trunk_point, branch_point, canvas, theme)

    path_kwargs: dict = {
        "stroke": color,
        "stroke_width": theme.branch_line_width,
        "fill": "none",
        "stroke_linecap": "round",
    }
    if stroke_dasharray is not None:
        path_kwargs["stroke_dasharray"] = stroke_dasharray

    path = draw.Path(**path_kwargs)
    builders = _LANE_CHANGE_BUILDERS if kind is LayoutArcKind.LANE_CHANGE else _CONNECTOR_BUILDERS
    builders[theme.branch_line_style](path, geom)
    d.append(path)
