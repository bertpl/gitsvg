"""Tests for the `merge` op state-apply handler."""

from tests._jsonl import build_jsonl
from tests.state._helpers import build_state_from_jsonl


def test_merge_creates_two_parent_commit_on_into_branch() -> None:
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "m1", "msg": "x"},
        {"op": "branch", "name": "feat", "from_branch": "main"},
        {"op": "commit", "branch": "feat", "id": "f1", "msg": "x"},
        {"op": "merge", "from": "feat", "into": "main", "as": "merge1"},
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    merge = state.commits["merge1"]
    assert merge.branch == "main"
    assert set(merge.parents) == {"m1", "f1"}
    assert state.branches["main"].commit_ids[-1] == "merge1"


def test_merge_into_empty_branch_uses_rooted_on_as_chain_parent() -> None:
    """Merging into a never-committed branch: the into-side parent is the
    branch's rooted-on commit (its chain parent), placed first — canonical
    chain-first, not dropped as a missing tip."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "branch", "name": "target", "from_commit": "c1"},
        {"op": "branch", "name": "feat", "from_commit": "c1"},
        {"op": "commit", "branch": "feat", "id": "f1", "msg": "x"},
        {"op": "merge", "from": "feat", "into": "target", "as": "mg"},
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    # target had no commits, so its chain parent is its rooted-on commit c1.
    assert state.commits["mg"].parents == ["c1", "f1"]


def test_merge_from_empty_rooted_branch_uses_its_branch_off_commit_as_second_parent() -> None:
    """Merging from a branch with no commits of its own: the from-side parent is
    the commit that branch points at (its branch-off commit), not dropped — so
    the result is a real two-parent merge."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c2", "msg": "y"},
        {"op": "branch", "name": "feat", "from_commit": "c1"},
        {"op": "merge", "from": "feat", "into": "main", "as": "mg"},
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    # feat has no commits, so its ref points at c1 → second parent, not dropped.
    assert state.commits["mg"].parents == ["c2", "c1"]


def test_self_merge_from_equals_into_emits_e209() -> None:
    # Merging a branch into itself is rejected (mirrors the E210 pull_request guard);
    # previously it silently produced a degenerate single-parent commit.
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "a"},
        {"op": "merge", "from": "main", "into": "main"},
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E209"]
    assert list(state.commits) == ["c1"]  # rejected before any merge commit is added


def test_merge_with_unknown_from_branch_emits_e200() -> None:
    # --- arrange ----------------------
    text = build_jsonl({"op": "branch", "name": "main"}, {"op": "merge", "from": "ghost", "into": "main"})

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E200"]


def test_merge_with_unknown_into_branch_emits_e200() -> None:
    # --- arrange ----------------------
    text = build_jsonl({"op": "branch", "name": "main"}, {"op": "merge", "from": "main", "into": "ghost"})

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E200"]


def test_merge_with_explicit_as_id_already_used_emits_e203() -> None:
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "m1", "msg": "x"},
        {"op": "branch", "name": "feat", "from_branch": "main"},
        {"op": "commit", "branch": "feat", "id": "f1", "msg": "x"},
        {"op": "merge", "from": "feat", "into": "main", "as": "m1"},
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E203"]


def test_merge_auto_generates_id_when_as_omitted() -> None:
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "m1", "msg": "x"},
        {"op": "branch", "name": "feat", "from_branch": "main"},
        {"op": "commit", "branch": "feat", "id": "f1", "msg": "x"},
        {"op": "merge", "from": "feat", "into": "main"},
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert len(state.branches["main"].commit_ids) == 2
    auto_id = state.branches["main"].commit_ids[-1]
    assert auto_id.startswith("_c")
