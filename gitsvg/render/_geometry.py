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

_GUIDE_OVERSHOOT_PX = 10  # axis-bound: commit-axis (applied symmetrically at both ends)


def branch_axis_to_x(pos: int, canvas: RenderCanvas) -> float:
    """Return the x pixel coordinate for a branch-axis index."""
    return canvas.margin_branch_axis_lower + pos * canvas.branch_spacing


def commit_axis_to_y(pos: int, canvas: RenderCanvas) -> float:
    """Return the y pixel coordinate for a commit-axis index."""
    return canvas.margin_commit_axis_upper + (canvas.n_commits - 1 - pos) * canvas.commit_spacing


def offset_position(
    anchor_branch_pos: int,
    anchor_commit_pos: int,
    branch_axis_offset_px: float,
    commit_axis_offset_px: float,
    canvas: RenderCanvas,
) -> tuple[float, float]:
    """Return the SVG `(x, y)` for a slot anchor plus pixel offsets along each axis.

    The offsets are pixel values in BT-relative direction:
    `branch_axis_offset_px` adds to screen x (positive = rightward),
    `commit_axis_offset_px` adds to screen y (positive = downward,
    toward lower commit-axis index in BT). The signed-axis-index
    convention lands on top in a later refactor.

    Args:
        anchor_branch_pos: Slot index along the branch axis the
            offset is anchored at.
        anchor_commit_pos: Slot index along the commit axis the
            offset is anchored at.
        branch_axis_offset_px: Pixel offset along screen x.
        commit_axis_offset_px: Pixel offset along screen y.
        canvas: Effective canvas spec for the geometry transforms.

    Returns:
        The resulting `(x, y)` in SVG pixel coordinates.
    """
    x = branch_axis_to_x(anchor_branch_pos, canvas) + branch_axis_offset_px
    y = commit_axis_to_y(anchor_commit_pos, canvas) + commit_axis_offset_px
    return (x, y)


def branch_guide_endpoints(canvas: RenderCanvas) -> tuple[float, float]:
    """Return the `(y_top, y_bottom)` span for branch guides on this canvas.

    Guides span the full canvas content area along the commit axis,
    with a small overshoot above and below the margin edges.

    Args:
        canvas: Effective canvas spec — the guide span depends on
            the commit-axis margins (which set the content edges)
            and the canvas height.

    Returns:
        A `(y_top, y_bottom)` pair in SVG pixel coordinates. `y_top`
        sits above the upper-margin edge; `y_bottom` sits below the
        lower-margin edge; both extend by `_GUIDE_OVERSHOOT_PX`.
    """
    y_top = canvas.margin_commit_axis_upper - _GUIDE_OVERSHOOT_PX
    y_bottom = canvas.height - canvas.margin_commit_axis_lower + _GUIDE_OVERSHOOT_PX
    return (y_top, y_bottom)
