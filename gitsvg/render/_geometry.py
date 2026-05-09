"""Coordinate transforms — layout positions to SVG pixel coordinates.

The transforms read effective spacing and margins from the
`LayoutCanvas` they're given, so per-frame `canvas:` op overrides
flow through naturally without the renderer needing constants.

Hard-coded bottom-to-top orientation: commit-axis index 0 sits at the
bottom of the canvas (oldest); higher indices sit higher (newer);
branch-axis index 0 sits at the left.
"""

from gitsvg.layout import LayoutCanvas


def branch_axis_to_x(pos: int, canvas: LayoutCanvas) -> float:
    """Return the x pixel coordinate for a branch-axis index."""
    return canvas.margin_branch_axis_lower + pos * canvas.branch_spacing


def commit_axis_to_y(pos: int, canvas: LayoutCanvas) -> float:
    """Return the y pixel coordinate for a commit-axis index."""
    return canvas.margin_commit_axis_upper + (canvas.n_commits - 1 - pos) * canvas.commit_spacing
