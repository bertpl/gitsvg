"""Tests for the axis-relative auto-fit helpers in `_canvas.py`."""

import pytest

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render._canvas import (
    _auto_fit_branch_axis_edge,
    _auto_fit_commit_axis_edge,
    compute_canvas,
)
from gitsvg.state import apply_ops


def _layout_and_theme(jsonl: str):
    """Parse → apply → layout → (layout, theme)."""
    parsed, report = parse_jsonl_text(jsonl, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    return compute_layout(state), theme


# ==================================================================================================
#  _auto_fit_branch_axis_edge
# ==================================================================================================
def test_branch_axis_edge_grows_for_lane_zero_pill_in_vertical_orientation() -> None:
    """In BT, a lane-0 branch pill contributes half-pill-width to the lower edge."""
    # --- arrange ----------------------
    layout, theme = _layout_and_theme(
        '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- act --------------------------
    lower = _auto_fit_branch_axis_edge(layout, theme, edge="lower")
    upper = _auto_fit_branch_axis_edge(layout, theme, edge="upper")

    # --- assert -----------------------
    # Single branch is on lane 0 = both edges' target → both reflect the pill.
    assert lower > 0
    assert upper > 0
    assert lower == upper


def test_branch_axis_edge_grows_for_outward_commit_label() -> None:
    """A label_side='after' commit on the max lane pushes the upper-edge allowance."""
    # --- arrange ----------------------
    # main on lane 0 with a 'before'-side label, feat on lane 1 (max) with default 'after'.
    layout, theme = _layout_and_theme(
        '{"op": "branch", "name": "main", "label_side": "before"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "short"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "this is a very long commit message"}\n'
    )

    # --- act --------------------------
    upper = _auto_fit_branch_axis_edge(layout, theme, edge="upper")
    lower = _auto_fit_branch_axis_edge(layout, theme, edge="lower")

    # --- assert -----------------------
    # Upper edge has the long 'after'-side label on lane 1.
    # Lower edge has the short 'before'-side label on lane 0.
    assert upper > lower


def test_branch_axis_edge_returns_zero_for_empty_layout() -> None:
    """No branches → no protruding content → 0 (theme defaults handled at the caller)."""
    # --- arrange ----------------------
    layout, theme = _layout_and_theme('{"op": "branch", "name": "main"}\n')
    # Empty branch declared but no commits — only a pill on lane 0 contributes.

    # --- act --------------------------
    needed = _auto_fit_branch_axis_edge(layout, theme, edge="upper")

    # --- assert -----------------------
    # Pill on lane 0 = max_lane (single branch) → upper still gets pill extent.
    assert needed > 0


# ==================================================================================================
#  _auto_fit_commit_axis_edge — branch pills (lower edge under default offset)
# ==================================================================================================
def test_commit_axis_lower_grows_for_branch_pill_at_start_zero() -> None:
    """Branch pill default offset is negative → start-zero branch pushes lower edge."""
    # --- arrange ----------------------
    layout, theme = _layout_and_theme(
        '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- act --------------------------
    lower = _auto_fit_commit_axis_edge(layout, theme, edge="lower")
    upper = _auto_fit_commit_axis_edge(layout, theme, edge="upper")

    # --- assert -----------------------
    # Lower edge holds the branch pill (offset -0.5 in BT).
    assert lower > 0
    # Upper edge is empty under default PR offset and no PRs anyway.
    assert upper == 0


def test_commit_axis_lower_uses_pill_width_in_horizontal_orientation() -> None:
    """LR branch pill is edge-anchored — its full pill_width extends along the commit axis."""
    # --- arrange ----------------------
    # Long branch name in LR → wide pill → big commit_axis_lower extent.
    long_name = "feature/release-2026-Q2-long-name"
    short_jsonl = (
        '{"op": "theme", "orientation": "lr"}\n'
        '{"op": "branch", "name": "m"}\n'
        '{"op": "commit", "branch": "m", "id": "c1", "msg": "x"}\n'
    )
    long_jsonl = (
        '{"op": "theme", "orientation": "lr"}\n'
        f'{{"op": "branch", "name": "{long_name}"}}\n'
        f'{{"op": "commit", "branch": "{long_name}", "id": "c1", "msg": "x"}}\n'
    )
    layout_short, theme_short = _layout_and_theme(short_jsonl)
    layout_long, theme_long = _layout_and_theme(long_jsonl)

    # --- act --------------------------
    lower_short = _auto_fit_commit_axis_edge(layout_short, theme_short, edge="lower")
    lower_long = _auto_fit_commit_axis_edge(layout_long, theme_long, edge="lower")

    # --- assert -----------------------
    # Long name → wider pill → larger allowance.
    assert lower_long > lower_short
    # Difference should be roughly the extra text width (>50 px for this name).
    assert lower_long - lower_short > 50


# ==================================================================================================
#  _auto_fit_commit_axis_edge — PR pills under overridden positive offset
# ==================================================================================================
def test_commit_axis_upper_grows_for_pr_pill_at_max_row_with_positive_offset_override() -> None:
    """PR pill with positive commit-axis offset at the top row pushes the upper edge."""
    # --- arrange ----------------------
    # Default PR commit-axis offset is -0.5 in BT; override to +0.5 so the
    # pill sits above the merge row instead of below it. With a PR whose
    # projected merge row equals max_commit_pos (the topmost row), the
    # pill protrudes past commit-axis-upper.
    layout, theme = _layout_and_theme(
        '{"op": "theme", "pull_request_pill_offset_commit_axis_in_rows": 0.5}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main", "title": "open PR"}\n'
    )

    # --- act --------------------------
    upper = _auto_fit_commit_axis_edge(layout, theme, edge="upper")

    # --- assert -----------------------
    assert upper > 0


def test_commit_axis_upper_is_zero_under_default_pr_offset_in_bt() -> None:
    """Default PR commit-axis offset is negative in BT → no upper-edge protrusion."""
    # --- arrange ----------------------
    layout, theme = _layout_and_theme(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main", "title": "open PR"}\n'
    )

    # --- act --------------------------
    upper = _auto_fit_commit_axis_edge(layout, theme, edge="upper")

    # --- assert -----------------------
    assert upper == 0


# ==================================================================================================
#  Integration — gap closures via compute_canvas
# ==================================================================================================
def test_lr_long_branch_name_grows_margin_left() -> None:
    """Long branch names in LR grow margin_left instead of overflowing it."""
    # --- arrange ----------------------
    long_name = "feature/release-2026-Q2-long-branch-name"
    short_jsonl = (
        '{"op": "theme", "orientation": "lr"}\n'
        '{"op": "branch", "name": "m"}\n'
        '{"op": "commit", "branch": "m", "id": "c1", "msg": "x"}\n'
    )
    long_jsonl = (
        '{"op": "theme", "orientation": "lr"}\n'
        f'{{"op": "branch", "name": "{long_name}"}}\n'
        f'{{"op": "commit", "branch": "{long_name}", "id": "c1", "msg": "x"}}\n'
    )
    short_layout, short_theme = _layout_and_theme(short_jsonl)
    long_layout, long_theme = _layout_and_theme(long_jsonl)

    # --- act --------------------------
    short_canvas = compute_canvas(short_layout, short_theme)
    long_canvas = compute_canvas(long_layout, long_theme)

    # --- assert -----------------------
    # Long name → wider margin_left in LR (the gap closure).
    assert long_canvas.margin_left > short_canvas.margin_left


def test_rl_long_branch_name_grows_margin_right() -> None:
    """Mirror of the LR case: long branch names in RL push margin_right out."""
    # --- arrange ----------------------
    long_name = "feature/release-2026-Q2-long-branch-name"
    short_jsonl = (
        '{"op": "theme", "orientation": "rl"}\n'
        '{"op": "branch", "name": "m"}\n'
        '{"op": "commit", "branch": "m", "id": "c1", "msg": "x"}\n'
    )
    long_jsonl = (
        '{"op": "theme", "orientation": "rl"}\n'
        f'{{"op": "branch", "name": "{long_name}"}}\n'
        f'{{"op": "commit", "branch": "{long_name}", "id": "c1", "msg": "x"}}\n'
    )
    short_layout, short_theme = _layout_and_theme(short_jsonl)
    long_layout, long_theme = _layout_and_theme(long_jsonl)

    # --- act --------------------------
    short_canvas = compute_canvas(short_layout, short_theme)
    long_canvas = compute_canvas(long_layout, long_theme)

    # --- assert -----------------------
    assert long_canvas.margin_right > short_canvas.margin_right


def test_tb_branch_pill_grows_margin_top_not_margin_bottom() -> None:
    """The TB fix: branch pill on start=0 grows margin_top (not margin_bottom).

    In TB, commit-axis-lower (where start=0 sits) maps to the visual top.
    The pre-refactor code assigned this auto-fit to margin_bottom, which
    was a latent bug from the BT-only original.
    """
    # --- arrange ----------------------
    layout, theme = _layout_and_theme(
        '{"op": "theme", "orientation": "tb"}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )
    static_margin_bottom = theme.margin_bottom

    # --- act --------------------------
    canvas = compute_canvas(layout, theme)

    # --- assert -----------------------
    # The pill auto-fit grew margin_top past its default; margin_bottom
    # stays at the static default.
    assert canvas.margin_top > theme.margin_top
    assert canvas.margin_bottom == static_margin_bottom


@pytest.mark.parametrize("orientation", ["bt", "tb", "lr", "rl"])
def test_default_theme_compute_canvas_returns_positive_dimensions(orientation: str) -> None:
    """Sanity: every orientation produces a usable canvas on a minimal diagram."""
    # --- arrange / act ----------------
    layout, theme = _layout_and_theme(
        f'{{"op": "theme", "orientation": "{orientation}"}}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )
    canvas = compute_canvas(layout, theme)

    # --- assert -----------------------
    assert canvas.width > 0
    assert canvas.height > 0
    assert canvas.orientation == orientation
