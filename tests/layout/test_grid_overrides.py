"""Tests for `grid:` op overrides — slot-count pins flow through to the layout extent.

Spacing and margin pins live on `theme:` (per invariant #6 — see
`docs/architecture.md` and `tests/state/test_apply_theme.py`); the
`grid:` op is slot counts only.
"""

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render._canvas import compute_canvas
from gitsvg.render._theme import build_theme
from gitsvg.state import apply_ops


def _layout_and_canvas(text: str):
    """Run the validate → state → layout → theme → render-canvas pipeline.

    Returns the `(layout, theme, render_canvas)` triple so individual tests
    can assert against the right surface.
    """
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state = apply_ops(parsed, report)
    layout = compute_layout(state)
    theme = build_theme(state)
    return layout, theme, compute_canvas(layout, theme)


# ==================================================================================================
#  n_commits / n_branches overrides (slot counts)
# ==================================================================================================
def test_grid_n_commits_override_pins_slot_count() -> None:
    """`grid.n_commits` pins the commit-axis slot count even when content has fewer commits."""
    # --- arrange / act ----------------
    layout, _, _ = _layout_and_canvas(
        '{"op": "grid", "n_commits": 10}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- assert -----------------------
    assert layout.grid.n_commits == 10


def test_grid_n_branches_override_pins_lane_count() -> None:
    """`grid.n_branches` pins the branch-axis slot count even when fewer lanes are used."""
    # --- arrange / act ----------------
    layout, _, _ = _layout_and_canvas('{"op": "grid", "n_branches": 5}\n{"op": "branch", "name": "main"}\n')

    # --- assert -----------------------
    assert layout.grid.n_branches == 5


# ==================================================================================================
#  Pinned grid + theme spacing → exact pixel canvas size
# ==================================================================================================
def test_pinned_grid_and_theme_spacing_govern_canvas_size() -> None:
    """A `grid:` op pinning slot counts + a `theme:` op pinning spacing/margins
    produces a canvas of exactly the expected pixel size, regardless of content."""
    # --- arrange / act ----------------
    _, _, canvas = _layout_and_canvas(
        '{"op": "grid", "n_commits": 12, "n_branches": 4}\n'
        '{"op": "theme", "commit_spacing": 50, "branch_spacing": 100, '
        '"margin_branch_axis_lower": 80, "margin_branch_axis_upper": 100, '
        '"margin_commit_axis_lower": 60, "margin_commit_axis_upper": 30}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- assert -----------------------
    # width = 80 + (4-1)*100 + 100 = 480.
    # height = 30 + (12-1)*50 + 60 = 640.
    assert canvas.width == 480
    assert canvas.height == 640


# ==================================================================================================
#  Auto-fit margins for long labels (renderer behaviour, no `grid:` op needed)
# ==================================================================================================
def test_long_branch_name_auto_fits_lower_margin_when_default_too_small() -> None:
    """A pill on the leftmost lane with a long name auto-extends the lower
    branch-axis margin so the pill doesn't clip past the canvas left edge."""
    # --- arrange ----------------------
    # Default margin is 100. A pill with half-width > 100 should extend the margin.
    # 200 chars * 11 * 0.58 / 2 = 638 px half-width — comfortably more than 100.
    long_name = "a" * 200
    text = f'{{"op": "branch", "name": "{long_name}"}}\n'

    # --- act --------------------------
    _, _, canvas = _layout_and_canvas(text)

    # --- assert -----------------------
    assert canvas.margin_branch_axis_lower > 100


def test_long_right_label_auto_fits_upper_margin() -> None:
    """A long right-side commit msg on the rightmost lane extends the upper
    branch-axis margin."""
    # --- arrange ----------------------
    long_msg = "a" * 50  # 50 chars * 11 * 0.58 ≈ 319 px — past default 100 + LABEL_OFFSET.
    text = (
        f'{{"op": "branch", "name": "main"}}\n{{"op": "commit", "branch": "main", "id": "c1", "msg": "{long_msg}"}}\n'
    )

    # --- act --------------------------
    _, _, canvas = _layout_and_canvas(text)

    # --- assert -----------------------
    # main is on lane 0 with default label_side="right", so the long label extends
    # into the *upper* margin (right side).
    assert canvas.margin_branch_axis_upper > 100
