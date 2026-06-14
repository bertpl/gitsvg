"""Tests for the `is_merge` flag on layout commits (set from parent count)."""

from gitsvg.layout import Layout, compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from tests._jsonl import build_jsonl


def _layout_from(text: str) -> Layout:
    """Parse JSONL → state → layout."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    return compute_layout(state)


def test_ordinary_commits_are_not_merges() -> None:
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c2", "msg": "x"},
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.commits["c1"].is_merge is False
    assert layout.commits["c2"].is_merge is False


def test_merge_commit_is_flagged() -> None:
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "m1", "msg": "x"},
        {"op": "branch", "name": "feat", "from_branch": "main"},
        {"op": "commit", "branch": "feat", "id": "f1", "msg": "x"},
        {"op": "merge", "from": "feat", "into": "main", "as": "mg"},
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.commits["mg"].is_merge is True
    assert layout.commits["m1"].is_merge is False
