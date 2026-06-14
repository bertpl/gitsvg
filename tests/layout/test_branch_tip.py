"""Tests for `LayoutBranch.tip_commit_id` — the commit a branch's ref points at.

Mirrors git's ref semantics: a non-empty branch's ref points at its last
commit; an empty branch's at its branch-off commit; a never-committed first
branch has no ref target. A commit may be the ref target of several branches.
"""

from gitsvg.layout import compute_layout, layout_to_json
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from tests._jsonl import build_jsonl


def _branches(text: str) -> dict:
    """Parse JSONL → state → layout, returning `{branch_name: LayoutBranch}`."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    return {b.name: b for b in compute_layout(state).branches}


def test_committed_branch_tip_is_its_last_commit() -> None:
    # --- arrange / act ----------------
    branches = _branches(
        build_jsonl(
            {"op": "branch", "name": "main"},
            {"op": "commit", "branch": "main", "id": "c1", "msg": "a"},
            {"op": "commit", "branch": "main", "id": "c2", "msg": "b"},
        )
    )

    # --- assert -----------------------
    assert branches["main"].tip_commit_id == "c2"


def test_empty_branch_tip_is_its_branch_off_commit_shared_with_parent() -> None:
    """An empty branch's ref points at the branch-off commit — a row shared with its parent."""
    # --- arrange / act ----------------
    branches = _branches(
        build_jsonl(
            {"op": "branch", "name": "main"},
            {"op": "commit", "branch": "main", "id": "c1", "msg": "a"},
            {"op": "branch", "name": "feature", "from_branch": "main"},
        )
    )

    # --- assert -----------------------
    # Both refs point at c1 → the multi-pill case.
    assert branches["main"].tip_commit_id == "c1"
    assert branches["feature"].tip_commit_id == "c1"


def test_never_committed_first_branch_has_no_tip() -> None:
    # --- arrange / act ----------------
    branches = _branches(build_jsonl({"op": "branch", "name": "main"}))

    # --- assert -----------------------
    assert branches["main"].tip_commit_id is None


def test_merge_leaves_source_tip_at_its_own_commit_and_target_at_the_merge() -> None:
    """The merged source's ref stays at its pre-merge commit; the target's ref is the merge commit."""
    # --- arrange / act ----------------
    branches = _branches(
        build_jsonl(
            {"op": "branch", "name": "main"},
            {"op": "commit", "branch": "main", "id": "c1", "msg": "a"},
            {"op": "branch", "name": "feature", "from_branch": "main"},
            {"op": "commit", "branch": "feature", "id": "f1", "msg": "b"},
            {"op": "merge", "from": "feature", "into": "main", "as": "m1", "msg": "merge"},
        )
    )

    # --- assert -----------------------
    assert branches["feature"].tip_commit_id == "f1"  # NOT the merge commit
    assert branches["main"].tip_commit_id == "m1"  # the merge commit is the target's tip


def test_tip_commit_id_is_serialized_in_layout_json() -> None:
    # --- arrange ----------------------
    parsed, report = parse_jsonl_text(
        build_jsonl({"op": "branch", "name": "main"}, {"op": "commit", "branch": "main", "id": "c1", "msg": "a"}),
        file="x.jsonl",
    )
    state, _theme = apply_ops(parsed, report)

    # --- act --------------------------
    payload = layout_to_json(compute_layout(state))

    # --- assert -----------------------
    assert payload["branches"][0]["tip_commit_id"] == "c1"
