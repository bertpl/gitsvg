"""Tests for coordinate transforms — branch axis → x, commit axis → y."""

from gitsvg._visual_constants import (
    BRANCH_SPACING,
    COMMIT_SPACING,
    MARGIN_BRANCH_AXIS_LOWER,
    MARGIN_BRANCH_AXIS_UPPER,
    MARGIN_COMMIT_AXIS_LOWER,
    MARGIN_COMMIT_AXIS_UPPER,
)
from gitsvg.layout import LayoutCanvas
from gitsvg.render._geometry import branch_axis_to_x, commit_axis_to_y


def _canvas(n_commits: int = 3) -> LayoutCanvas:
    """Build a minimal LayoutCanvas with the default visual constants."""
    width = MARGIN_BRANCH_AXIS_LOWER + MARGIN_BRANCH_AXIS_UPPER
    height = MARGIN_COMMIT_AXIS_UPPER + (n_commits - 1) * COMMIT_SPACING + MARGIN_COMMIT_AXIS_LOWER
    return LayoutCanvas(
        width=width,
        height=height,
        n_commits=n_commits,
        n_branches=1,
        branch_spacing=BRANCH_SPACING,
        commit_spacing=COMMIT_SPACING,
        margin_branch_axis_lower=MARGIN_BRANCH_AXIS_LOWER,
        margin_branch_axis_upper=MARGIN_BRANCH_AXIS_UPPER,
        margin_commit_axis_lower=MARGIN_COMMIT_AXIS_LOWER,
        margin_commit_axis_upper=MARGIN_COMMIT_AXIS_UPPER,
    )


def test_branch_axis_index_zero_lands_at_lower_margin() -> None:
    # --- act / assert -----------------
    assert branch_axis_to_x(0, _canvas()) == MARGIN_BRANCH_AXIS_LOWER


def test_branch_axis_increments_by_branch_spacing() -> None:
    # --- act / assert -----------------
    assert branch_axis_to_x(2, _canvas()) == MARGIN_BRANCH_AXIS_LOWER + 2 * BRANCH_SPACING


def test_commit_axis_top_index_lands_at_upper_margin() -> None:
    """The newest commit (highest index) sits at the top of the canvas."""
    # --- act / assert -----------------
    assert commit_axis_to_y(2, _canvas(3)) == MARGIN_COMMIT_AXIS_UPPER


def test_commit_axis_index_zero_is_at_bottom_of_canvas() -> None:
    """Index 0 is the oldest commit; bottom-to-top puts it at the largest y."""
    # --- act / assert -----------------
    assert commit_axis_to_y(0, _canvas(3)) == MARGIN_COMMIT_AXIS_UPPER + 2 * COMMIT_SPACING


def test_commit_axis_step_size_equals_commit_spacing() -> None:
    # --- act --------------------------
    canvas = _canvas(5)
    y_at_0 = commit_axis_to_y(0, canvas)
    y_at_1 = commit_axis_to_y(1, canvas)

    # --- assert -----------------------
    assert y_at_0 - y_at_1 == COMMIT_SPACING


def test_geometry_uses_canvas_overrides_when_set() -> None:
    """Effective spacing/margins on the canvas object flow through the
    transform — the renderer doesn't re-read constants."""
    # --- arrange ----------------------
    canvas = LayoutCanvas(
        width=500,
        height=500,
        n_commits=4,
        n_branches=2,
        branch_spacing=80,  # custom override
        commit_spacing=40,  # custom override
        margin_branch_axis_lower=50,  # custom override
        margin_branch_axis_upper=50,
        margin_commit_axis_lower=30,
        margin_commit_axis_upper=30,
    )

    # --- act / assert -----------------
    assert branch_axis_to_x(1, canvas) == 50 + 1 * 80
    # Commit-axis: y = margin_upper + (n_commits - 1 - pos) * commit_spacing.
    assert commit_axis_to_y(0, canvas) == 30 + (4 - 1) * 40
    assert commit_axis_to_y(3, canvas) == 30
