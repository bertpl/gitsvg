"""Tests for coordinate transforms — `grid_to_pixel` per orientation."""

import copy

from gitsvg.render._canvas import RenderCanvas
from gitsvg.render._geometry import grid_to_pixel
from gitsvg.theme import DEFAULT_THEME, resolve_defaults


def _resolved_default_theme():
    """Return a deep copy of `DEFAULT_THEME` with the resolver applied."""
    theme = copy.deepcopy(DEFAULT_THEME)
    resolve_defaults(theme)
    return theme


def _canvas(n_commits: int = 3) -> RenderCanvas:
    """Build a minimal `RenderCanvas` matching the resolved-default-theme constants (BT)."""
    theme = _resolved_default_theme()
    width = theme.margin_left + theme.margin_right
    height = theme.margin_top + (n_commits - 1) * theme.commit_spacing + theme.margin_bottom
    return RenderCanvas(
        width=width,
        height=height,
        n_commits=n_commits,
        n_branches=1,
        branch_spacing=theme.branch_spacing,
        commit_spacing=theme.commit_spacing,
        margin_left=theme.margin_left,
        margin_right=theme.margin_right,
        margin_bottom=theme.margin_bottom,
        margin_top=theme.margin_top,
        orientation=theme.orientation,
    )


# ==================================================================================================
#  BT (default orientation) — preserves byte-identical baseline
# ==================================================================================================
def test_branch_axis_index_zero_lands_at_left_margin_in_bt() -> None:
    # --- act / assert -----------------
    x, _ = grid_to_pixel(0, 0, _canvas())
    assert x == _resolved_default_theme().margin_left


def test_branch_axis_increments_by_branch_spacing_in_bt() -> None:
    # --- act / assert -----------------
    theme = _resolved_default_theme()
    x, _ = grid_to_pixel(2, 0, _canvas())
    assert x == theme.margin_left + 2 * theme.branch_spacing


def test_commit_axis_top_index_lands_at_top_margin_in_bt() -> None:
    """The newest commit (highest index) sits at the top of the canvas."""
    # --- act / assert -----------------
    _, y = grid_to_pixel(0, 2, _canvas(3))
    assert y == _resolved_default_theme().margin_top


def test_commit_axis_index_zero_is_at_bottom_of_canvas_in_bt() -> None:
    """Index 0 is the oldest commit; bottom-to-top puts it at the largest y."""
    # --- act / assert -----------------
    theme = _resolved_default_theme()
    _, y = grid_to_pixel(0, 0, _canvas(3))
    assert y == theme.margin_top + 2 * theme.commit_spacing


def test_commit_axis_step_size_equals_commit_spacing_in_bt() -> None:
    # --- act --------------------------
    canvas = _canvas(5)
    _, y_at_0 = grid_to_pixel(0, 0, canvas)
    _, y_at_1 = grid_to_pixel(0, 1, canvas)

    # --- assert -----------------------
    assert y_at_0 - y_at_1 == _resolved_default_theme().commit_spacing


def test_geometry_uses_canvas_overrides_when_set_in_bt() -> None:
    """Effective spacing/margins on the canvas object flow through the
    transform — the renderer doesn't re-read constants."""
    # --- arrange ----------------------
    canvas = RenderCanvas(
        width=500,
        height=500,
        n_commits=4,
        n_branches=2,
        branch_spacing=80,  # custom override
        commit_spacing=40,  # custom override
        margin_left=50,  # custom override
        margin_right=50,
        margin_bottom=30,
        margin_top=30,
        orientation="bt",
    )

    # --- act / assert -----------------
    x, _ = grid_to_pixel(1, 0, canvas)
    assert x == 50 + 1 * 80
    # Commit-axis: y = margin_top + (n_commits - 1 - pos) * commit_spacing.
    _, y_oldest = grid_to_pixel(0, 0, canvas)
    _, y_newest = grid_to_pixel(0, 3, canvas)
    assert y_oldest == 30 + (4 - 1) * 40
    assert y_newest == 30


# ==================================================================================================
#  Per-orientation paired transform — directional sanity checks
# ==================================================================================================
def _canvas_for(orientation: str) -> RenderCanvas:
    """Build a minimal `RenderCanvas` with explicit margins so each test
    can predict slot pixel positions independently of auto-fit."""
    return RenderCanvas(
        width=500,
        height=500,
        n_commits=4,
        n_branches=3,
        branch_spacing=80,
        commit_spacing=40,
        margin_left=50,
        margin_right=50,
        margin_bottom=30,
        margin_top=30,
        orientation=orientation,
    )


def test_tb_origin_is_top_left_with_commits_growing_down() -> None:
    # --- arrange ----------------------
    canvas = _canvas_for("tb")

    # --- act / assert -----------------
    # Slot (0, 0) at top-left: x=margin_left, y=margin_top.
    assert grid_to_pixel(0, 0, canvas) == (50, 30)
    # Commit-axis grows down: commit_pos=1 → y increases by commit_spacing.
    assert grid_to_pixel(0, 1, canvas) == (50, 30 + 40)
    # Branch-axis grows right: branch_pos=1 → x increases by branch_spacing.
    assert grid_to_pixel(1, 0, canvas) == (50 + 80, 30)


def test_lr_origin_is_top_left_with_commits_growing_right() -> None:
    # --- arrange ----------------------
    canvas = _canvas_for("lr")

    # --- act / assert -----------------
    # Slot (0, 0) at top-left.
    assert grid_to_pixel(0, 0, canvas) == (50, 30)
    # Commit-axis grows right: commit_pos=1 → x increases by commit_spacing.
    assert grid_to_pixel(0, 1, canvas) == (50 + 40, 30)
    # Branch-axis grows down: branch_pos=1 → y increases by branch_spacing.
    assert grid_to_pixel(1, 0, canvas) == (50, 30 + 80)


def test_rl_origin_is_top_right_with_commits_growing_left() -> None:
    # --- arrange ----------------------
    canvas = _canvas_for("rl")

    # --- act / assert -----------------
    # Slot (0, 0) at top-right: x = margin_left + (n_commits-1)*commit_spacing.
    # n_commits=4, commit_spacing=40 → 50 + 3*40 = 170.
    assert grid_to_pixel(0, 0, canvas) == (50 + 3 * 40, 30)
    # Commit-axis grows left: commit_pos=1 → x decreases by commit_spacing.
    assert grid_to_pixel(0, 1, canvas) == (50 + 3 * 40 - 40, 30)
    # Branch-axis grows down: same as LR.
    assert grid_to_pixel(1, 0, canvas) == (50 + 3 * 40, 30 + 80)
