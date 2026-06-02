"""Tests for the `is_merge` flag on layout commits (set from parent count)."""

from gitsvg.layout import Layout, compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops


def _layout_from(text: str) -> Layout:
    """Parse JSONL → state → layout."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    return compute_layout(state)


def test_ordinary_commits_are_not_merges() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.commits["c1"].is_merge is False
    assert layout.commits["c2"].is_merge is False


def test_merge_commit_is_flagged() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "mg"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.commits["mg"].is_merge is True
    assert layout.commits["m1"].is_merge is False
