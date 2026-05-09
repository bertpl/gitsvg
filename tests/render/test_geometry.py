"""Tests for coordinate transforms — branch axis → x, commit axis → y."""

from gitsvg._visual_constants import (
    BRANCH_SPACING,
    COMMIT_SPACING,
    MARGIN_BRANCH_AXIS_LOWER,
    MARGIN_COMMIT_AXIS_UPPER,
)
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y


def test_branch_axis_index_zero_lands_at_lower_margin() -> None:
    # --- act / assert -----------------
    assert branch_axis_to_x(0) == MARGIN_BRANCH_AXIS_LOWER


def test_branch_axis_increments_by_branch_spacing() -> None:
    # --- act / assert -----------------
    assert branch_axis_to_x(2) == MARGIN_BRANCH_AXIS_LOWER + 2 * BRANCH_SPACING


def test_commit_axis_top_index_lands_at_upper_margin() -> None:
    """The newest commit (highest index) sits at the top of the canvas."""
    # --- act / assert -----------------
    assert commit_axis_to_y(2, 3) == MARGIN_COMMIT_AXIS_UPPER


def test_commit_axis_index_zero_is_at_bottom_of_canvas() -> None:
    """Index 0 is the oldest commit; bottom-to-top puts it at the largest y."""
    # --- act / assert -----------------
    assert commit_axis_to_y(0, 3) == MARGIN_COMMIT_AXIS_UPPER + 2 * COMMIT_SPACING


def test_commit_axis_step_size_equals_commit_spacing() -> None:
    # --- act --------------------------
    y_at_0 = commit_axis_to_y(0, 5)
    y_at_1 = commit_axis_to_y(1, 5)

    # --- assert -----------------------
    assert y_at_0 - y_at_1 == COMMIT_SPACING
