"""Coordinate transforms — layout positions to SVG pixel coordinates.

The orientation is hard-coded bottom-to-top: commit-axis index 0 sits
at the bottom of the canvas (oldest), higher indices sit higher
(newer); branch-axis index 0 sits at the left.
"""

from gitsvg._visual_constants import (
    BRANCH_SPACING,
    COMMIT_SPACING,
    MARGIN_BRANCH_AXIS_LOWER,
    MARGIN_COMMIT_AXIS_UPPER,
)


def branch_axis_to_x(pos: int) -> float:
    """Return the x pixel coordinate for a branch-axis index.

    Args:
        pos: Branch-axis index, 0-based.

    Returns:
        The center-of-lane x coordinate in SVG pixel space.
    """
    return MARGIN_BRANCH_AXIS_LOWER + pos * BRANCH_SPACING


def commit_axis_to_y(pos: int, n_commits: int) -> float:
    """Return the y pixel coordinate for a commit-axis index.

    Args:
        pos: Commit-axis index, 0-based; 0 is the oldest.
        n_commits: Total number of commit-axis slots (= max
            commit-axis index + 1). Needed because the bottom-to-top
            orientation places index 0 at the largest y, so the
            transform must know the canvas height implicitly.

    Returns:
        The center-of-row y coordinate in SVG pixel space.
    """
    return MARGIN_COMMIT_AXIS_UPPER + (n_commits - 1 - pos) * COMMIT_SPACING
