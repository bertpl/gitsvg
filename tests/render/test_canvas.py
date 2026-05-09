"""Tests for canvas-size auto-fit (PR4 only — no `canvas:` op honouring yet)."""

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render._canvas import compute_canvas_size
from gitsvg.render._constants import (
    BRANCH_SPACING,
    COMMIT_SPACING,
    MARGIN_BRANCH_AXIS_LOWER,
    MARGIN_BRANCH_AXIS_UPPER,
    MARGIN_COMMIT_AXIS_LOWER,
    MARGIN_COMMIT_AXIS_UPPER,
)


def _layout_from(text: str):
    parsed, _ = parse_jsonl_text(text, file="x.jsonl")
    return compute_layout(parsed)


def test_single_branch_with_three_commits_canvas_size() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
    )
    layout = _layout_from(text)

    # --- act --------------------------
    width, height, n_commits = compute_canvas_size(layout)

    # --- assert -----------------------
    # max_branch_pos = 0; width = 100 + 0*100 + 100 = 200.
    assert width == MARGIN_BRANCH_AXIS_LOWER + 0 * BRANCH_SPACING + MARGIN_BRANCH_AXIS_UPPER
    # n_commits = 3; height = 25 + (3-1)*50 + 25 = 150.
    assert n_commits == 3
    assert height == MARGIN_COMMIT_AXIS_UPPER + (3 - 1) * COMMIT_SPACING + MARGIN_COMMIT_AXIS_LOWER


def test_two_branches_widen_canvas() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
    )
    layout = _layout_from(text)

    # --- act --------------------------
    width, _, _ = compute_canvas_size(layout)

    # --- assert -----------------------
    # max_branch_pos = 1; width = 100 + 1*100 + 100 = 300.
    assert width == MARGIN_BRANCH_AXIS_LOWER + 1 * BRANCH_SPACING + MARGIN_BRANCH_AXIS_UPPER


def test_empty_branch_extends_canvas_when_start_is_above_commits() -> None:
    """An empty fork branch with start > max(commit_pos) still extends the canvas."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )
    layout = _layout_from(text)

    # --- act --------------------------
    _, height, n_commits = compute_canvas_size(layout)

    # --- assert -----------------------
    # main commits at 0, 1; feat.start = feat.end = 2 (no commits).
    # n_commits should be 3 to fit the empty branch's pill area.
    assert n_commits == 3
    assert height == MARGIN_COMMIT_AXIS_UPPER + (3 - 1) * COMMIT_SPACING + MARGIN_COMMIT_AXIS_LOWER
