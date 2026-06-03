"""Coordinate transforms — slot indices to SVG pixel coordinates.

The transforms read effective spacing, margins, and orientation from
a `RenderCanvas`. Per `docs/architecture.md` invariant #5 every
render-side coordinate computation routes through this module's
helpers; per invariant #7 every orientation-dependent decision lives
here too — primitives never branch on orientation directly.

Orientation table (mirrors invariant #7):

| Orientation | Origin (screen corner) | Commit-axis grows | Branch-axis grows |
|---|---|---|---|
| `bt` | bottom-left  | up    | right |
| `tb` | top-left     | down  | right |
| `lr` | top-left     | right | down  |
| `rl` | top-right    | left  | down  |

`grid_to_pixel` is the canonical paired transform. `offset_position`
applies a signed two-axis grid offset (positive = toward higher
index along the named axis) on top of an anchor.
`branch_line_endpoints` and `branch_guide_endpoints` return
orientation-aware screen endpoints for the two line-shaped
primitives.
"""

from gitsvg._shared.value_types import Orientation
from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._renderer_settings import RendererSettings
from gitsvg.theme import _resolve_int_or_float


def grid_to_pixel(branch_pos: int, commit_pos: int, canvas: RenderCanvas) -> tuple[float, float]:
    """Map a `(branch_pos, commit_pos)` grid position to its `(x, y)` pixel coordinates.

    The mapping depends on `canvas.orientation`. Bottom-to-top (`bt`)
    places commit-axis index 0 at the largest y; the other three
    orientations follow the table in this module's docstring.

    Returned types are the natural Python arithmetic types: x is `int`
    when both anchor margin and the spacing-multiplied offset are int
    (whole-number-input case in vertical orientations); y is always
    `float` because `compute_canvas` force-casts `margin_top` to float
    so the SVG y-attribute formatting stays consistent with the
    byte-identical baseline. Callers that apply pixel offsets after
    this transform (`offset_position`) cast each offset to int when
    whole independently.

    Args:
        branch_pos: Branch-axis index (integer slot position).
        commit_pos: Commit-axis index (integer slot position).
        canvas: Effective canvas spec — supplies margins, spacings,
            slot counts, and the active orientation.

    Returns:
        The `(x, y)` pixel coordinates.
    """
    if canvas.orientation == Orientation.BT:
        x = canvas.margin_left + branch_pos * canvas.branch_spacing
        y = canvas.margin_top + (canvas.n_commits - 1 - commit_pos) * canvas.commit_spacing
    elif canvas.orientation == Orientation.TB:
        x = canvas.margin_left + branch_pos * canvas.branch_spacing
        y = canvas.margin_top + commit_pos * canvas.commit_spacing
    elif canvas.orientation == Orientation.LR:
        x = canvas.margin_left + commit_pos * canvas.commit_spacing
        y = canvas.margin_top + branch_pos * canvas.branch_spacing
    else:  # rl
        x = canvas.margin_left + (canvas.n_commits - 1 - commit_pos) * canvas.commit_spacing
        y = canvas.margin_top + branch_pos * canvas.branch_spacing
    return (x, y)


def offset_position(
    anchor_branch_pos: int,
    anchor_commit_pos: int,
    branch_axis_offset_in_lanes: float,
    commit_axis_offset_in_rows: float,
    canvas: RenderCanvas,
) -> tuple[float, float]:
    """Return the SVG `(x, y)` for a slot anchor plus a signed two-axis offset.

    Both offsets follow the **signed grid-axis convention**: positive =
    toward higher index along the named axis (see invariant #3 in
    `docs/architecture.md`). The helper resolves each offset to a
    pixel offset along the matching grid axis, then maps the
    grid-direction offset to a screen-direction offset per the active
    orientation.

    Resolving the grid offsets to integer pixels (via
    `_resolve_int_or_float`) before adding to the anchor preserves
    int formatting in the SVG attribute output for whole-number
    offsets.

    Args:
        anchor_branch_pos: Slot index along the branch axis the
            offset is anchored at.
        anchor_commit_pos: Slot index along the commit axis the
            offset is anchored at.
        branch_axis_offset_in_lanes: Signed offset along the branch
            axis, expressed as a multiple of `branch_spacing`.
        commit_axis_offset_in_rows: Signed offset along the commit
            axis, expressed as a multiple of `commit_spacing`.
        canvas: Effective canvas spec for the geometry transforms.

    Returns:
        The resulting `(x, y)` in SVG pixel coordinates.
    """
    branch_offset_px = _resolve_int_or_float(branch_axis_offset_in_lanes * canvas.branch_spacing)
    commit_offset_px = _resolve_int_or_float(commit_axis_offset_in_rows * canvas.commit_spacing)
    anchor_x, anchor_y = grid_to_pixel(anchor_branch_pos, anchor_commit_pos, canvas)
    return _apply_pixel_offset(anchor_x, anchor_y, branch_offset_px, commit_offset_px, canvas.orientation)


def branch_line_endpoints(
    branch_pos: int,
    start_commit_pos: int,
    end_commit_pos: int,
    canvas: RenderCanvas,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the two screen endpoints of a branch line.

    The line spans the branch's commit-axis extent at a constant
    branch-axis position (the lane). In vertical orientations
    (`bt`, `tb`) the line is screen-vertical (constant x); in
    horizontal orientations (`lr`, `rl`) it is screen-horizontal
    (constant y).

    Args:
        branch_pos: The branch's lane index.
        start_commit_pos: Commit-axis index where the branch begins.
        end_commit_pos: Commit-axis index of the branch's tip.
        canvas: Effective canvas spec.

    Returns:
        `((x_start, y_start), (x_end, y_end))` — the two endpoints
        for `draw.Line`.
    """
    p_start = grid_to_pixel(branch_pos, start_commit_pos, canvas)
    p_end = grid_to_pixel(branch_pos, end_commit_pos, canvas)
    return (p_start, p_end)


def branch_guide_endpoints(
    branch_pos: int,
    canvas: RenderCanvas,
    theme: RendererSettings,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the two screen endpoints of a branch guide line for a single lane.

    The guide spans the full canvas content area along the commit
    axis with a small `theme.guide_overshoot` past the canvas
    margins on each end. Orientation determines whether the guide
    is screen-vertical (vertical orientations) or screen-horizontal
    (horizontal orientations).

    Args:
        branch_pos: The lane index the guide sits on.
        canvas: Effective canvas spec.
        theme: Resolved theme; supplies the overshoot value.

    Returns:
        `((x1, y1), (x2, y2))` — the two endpoints for the dashed
        guide line.
    """
    overshoot = theme.guide_overshoot
    if canvas.orientation.is_vertical:
        x = grid_to_pixel(branch_pos, 0, canvas)[0]
        y_top = canvas.margin_top - overshoot
        y_bottom = canvas.height - canvas.margin_bottom + overshoot
        return ((x, y_top), (x, y_bottom))
    # Horizontal orientations: guide is a horizontal line at the lane's y.
    y = grid_to_pixel(branch_pos, 0, canvas)[1]
    x_left = canvas.margin_left - overshoot
    x_right = canvas.width - canvas.margin_right + overshoot
    return ((x_left, y), (x_right, y))


def commit_row_band_rect(commit_pos: int, canvas: RenderCanvas) -> tuple[float, float, float, float]:
    """Return the `(x, y, width, height)` of a full-span band for one commit-axis row.

    The band spans the entire canvas perpendicular to the commit axis
    and is `commit_spacing` thick along it, centered on the row's screen
    position. In vertical orientations (`bt` / `tb`) it is a full-width
    horizontal stripe; in horizontal orientations (`lr` / `rl`) a
    full-height vertical stripe.

    Args:
        commit_pos: Commit-axis slot index of the row to band.
        canvas: Effective canvas spec — supplies span, spacing, and
            orientation.

    Returns:
        `(x, y, width, height)` for a `draw.Rectangle`.
    """
    thickness = canvas.commit_spacing
    center_x, center_y = grid_to_pixel(0, commit_pos, canvas)
    # The full-span origin coordinate is a literal int 0 (not 0.0) so the SVG
    # attribute reads `x="0"` / `y="0"`, matching the background rect's output.
    if canvas.orientation.is_vertical:
        return (0, center_y - thickness / 2, canvas.width, thickness)
    return (center_x - thickness / 2, 0, thickness, canvas.height)


# ==================================================================================================
#  Internals
# ==================================================================================================
def _apply_pixel_offset(
    x: float,
    y: float,
    branch_axis_offset_px: float,
    commit_axis_offset_px: float,
    orientation: Orientation,
) -> tuple[float, float]:
    """Add signed grid-axis offsets (in pixels) to an anchor position.

    Maps the (branch-axis, commit-axis) signed offset pair to a
    (dx, dy) screen offset per orientation. The mapping follows the
    table in this module's docstring: positive branch-axis offset
    moves toward higher branch-axis index (right in `bt`/`tb`, down
    in `lr`/`rl`); positive commit-axis offset moves toward higher
    commit-axis index (up in `bt`, down in `tb`, right in `lr`,
    left in `rl`).

    Args:
        x: Anchor x in pixels.
        y: Anchor y in pixels.
        branch_axis_offset_px: Signed pixel offset along branch axis.
        commit_axis_offset_px: Signed pixel offset along commit axis.
        orientation: Active orientation (`bt`, `tb`, `lr`, `rl`).

    Returns:
        The offset `(x, y)` position.
    """
    if orientation == Orientation.BT:
        return (x + branch_axis_offset_px, y - commit_axis_offset_px)
    if orientation == Orientation.TB:
        return (x + branch_axis_offset_px, y + commit_axis_offset_px)
    if orientation == Orientation.LR:
        return (x + commit_axis_offset_px, y + branch_axis_offset_px)
    # rl
    return (x - commit_axis_offset_px, y + branch_axis_offset_px)
