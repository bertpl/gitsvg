"""Tests for `canvas:` op overrides on layout."""

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops


def _layout_from(text: str):
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state = apply_ops(parsed, report)
    return compute_layout(state)


# ==================================================================================================
#  n_commits / n_branches overrides
# ==================================================================================================
def test_canvas_n_commits_override_pins_slot_count() -> None:
    """`canvas.n_commits` pins the commit-axis slot count even when content
    has fewer commits."""
    # --- arrange ----------------------
    text = (
        '{"op": "canvas", "n_commits": 10}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.canvas.n_commits == 10


def test_canvas_n_branches_override_pins_lane_count() -> None:
    # --- arrange ----------------------
    text = '{"op": "canvas", "n_branches": 5}\n{"op": "branch", "name": "main"}\n'

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.canvas.n_branches == 5


# ==================================================================================================
#  Spacing overrides
# ==================================================================================================
def test_canvas_branch_spacing_override() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "canvas", "branch_spacing": 80}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.canvas.branch_spacing == 80


def test_canvas_commit_spacing_override() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "canvas", "commit_spacing": 40}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.canvas.commit_spacing == 40


# ==================================================================================================
#  Margin overrides
# ==================================================================================================
def test_canvas_margin_overrides_all_four_axes() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "canvas", "margin_branch_axis_lower": 40, "margin_branch_axis_upper": 60, '
        '"margin_commit_axis_lower": 70, "margin_commit_axis_upper": 50}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.canvas.margin_branch_axis_lower == 40
    assert layout.canvas.margin_branch_axis_upper == 60
    assert layout.canvas.margin_commit_axis_lower == 70
    assert layout.canvas.margin_commit_axis_upper == 50


def test_canvas_pinned_dimensions_govern_canvas_size() -> None:
    """Pinned spacing + pinned slot counts produce a canvas of exactly the
    expected pinned size, regardless of content extent."""
    # --- arrange ----------------------
    text = (
        '{"op": "canvas", "n_commits": 12, "n_branches": 4, "commit_spacing": 50, '
        '"branch_spacing": 100, "margin_branch_axis_lower": 80, "margin_branch_axis_upper": 100, '
        '"margin_commit_axis_lower": 60, "margin_commit_axis_upper": 30}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # width = 80 + (4-1)*100 + 100 = 480.
    # height = 30 + (12-1)*50 + 60 = 640.
    assert layout.canvas.width == 480
    assert layout.canvas.height == 640


# ==================================================================================================
#  Auto-fit margins for long labels
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
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.canvas.margin_branch_axis_lower > 100


def test_long_right_label_auto_fits_upper_margin() -> None:
    """A long right-side commit msg on the rightmost lane extends the upper
    branch-axis margin."""
    # --- arrange ----------------------
    long_msg = "a" * 50  # 50 chars * 11 * 0.58 ≈ 319 px — past default 100 + LABEL_OFFSET.
    text = (
        f'{{"op": "branch", "name": "main"}}\n{{"op": "commit", "branch": "main", "id": "c1", "msg": "{long_msg}"}}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # main is on lane 0 with default label_side="right", so the long label extends
    # into the *upper* margin (right side).
    assert layout.canvas.margin_branch_axis_upper > 100
