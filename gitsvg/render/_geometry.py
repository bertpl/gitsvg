"""Coordinate transforms — slot indices to SVG pixel coordinates.

The transforms read effective spacing and margins from a
`RenderCanvas`, so per-frame `theme:` op overrides flow through
naturally.

Hard-coded bottom-to-top orientation: commit-axis index 0 sits at the
bottom of the canvas (oldest); higher indices sit higher (newer);
branch-axis index 0 sits at the left.

Per invariant #5 in `docs/architecture.md`, every render-side
coordinate computation routes through this module's helpers.
Primitives never assemble coordinates inline.
"""

from gitsvg.render._canvas import RenderCanvas
from gitsvg.theme import Theme, _resolve_int_or_float


def branch_axis_to_x(pos: int, canvas: RenderCanvas) -> float:
    """Return the x pixel coordinate for a branch-axis index."""
    return canvas.margin_left + pos * canvas.branch_spacing


def commit_axis_to_y(pos: int, canvas: RenderCanvas) -> float:
    """Return the y pixel coordinate for a commit-axis index."""
    return canvas.margin_top + (canvas.n_commits - 1 - pos) * canvas.commit_spacing


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
    `docs/architecture.md`). The helper multiplies each offset by the
    matching canvas spacing to get the pixel magnitude, then maps grid
    direction to screen direction. Currently supports only bottom-to-top
    orientation: positive branch-axis = `+x`; positive commit-axis = `-y`.

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
    # Cast whole-number offsets back to int so the SVG attribute formatting
    # matches the byte-identical baseline (int → `x="100"`, float → `x="100.0"`).
    branch_offset_px = _resolve_int_or_float(branch_axis_offset_in_lanes * canvas.branch_spacing)
    commit_offset_px = _resolve_int_or_float(commit_axis_offset_in_rows * canvas.commit_spacing)
    x = branch_axis_to_x(anchor_branch_pos, canvas) + branch_offset_px
    # Bottom-to-top: positive commit-axis index sits at lower screen y → subtract.
    y = commit_axis_to_y(anchor_commit_pos, canvas) - commit_offset_px
    return (x, y)


def branch_guide_endpoints(canvas: RenderCanvas, theme: Theme) -> tuple[float, float]:
    """Return the `(y_top, y_bottom)` span for branch guides on this canvas.

    Guides span the full canvas content area along the commit axis,
    with a small overshoot above and below the margin edges. The
    overshoot is `theme.guide_overshoot` — a resolved pixel value
    derived from `theme.guide_overshoot_in_rows × commit_spacing`.

    Args:
        canvas: Effective canvas spec — the guide span depends on
            the commit-axis margins (which set the content edges)
            and the canvas height.
        theme: Resolved theme; supplies the overshoot value.

    Returns:
        A `(y_top, y_bottom)` pair in SVG pixel coordinates. `y_top`
        sits `theme.guide_overshoot` px above the upper-margin edge;
        `y_bottom` sits the same distance below the lower-margin edge.
    """
    y_top = canvas.margin_top - theme.guide_overshoot
    y_bottom = canvas.height - canvas.margin_bottom + theme.guide_overshoot
    return (y_top, y_bottom)
