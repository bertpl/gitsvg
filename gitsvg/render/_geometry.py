"""Coordinate transforms — slot indices to SVG pixel coordinates.

The transforms read effective spacing and margins from a
`RenderCanvas`, so per-frame `canvas:` op overrides (folded into the
theme by `build_theme`) flow through naturally.

Hard-coded bottom-to-top orientation: commit-axis index 0 sits at the
bottom of the canvas (oldest); higher indices sit higher (newer);
branch-axis index 0 sits at the left.
"""

from gitsvg.render._canvas import RenderCanvas


def branch_axis_to_x(pos: int, canvas: RenderCanvas) -> float:
    """Return the x pixel coordinate for a branch-axis index."""
    return canvas.margin_branch_axis_lower + pos * canvas.branch_spacing


def commit_axis_to_y(pos: int, canvas: RenderCanvas) -> float:
    """Return the y pixel coordinate for a commit-axis index."""
    return canvas.margin_commit_axis_upper + (canvas.n_commits - 1 - pos) * canvas.commit_spacing
