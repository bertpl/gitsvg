"""Tests for the `merge` op state-apply handler."""

from tests.state._helpers import build_state_from_jsonl


def test_merge_creates_two_parent_commit_on_into_branch() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "merge1"}\n'
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    merge = state.commits["merge1"]
    assert merge.branch == "main"
    assert set(merge.parents) == {"m1", "f1"}
    assert state.branches["main"].commit_ids[-1] == "merge1"


def test_merge_with_unknown_from_branch_emits_e200() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "merge", "from": "ghost", "into": "main"}\n'

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E200"]


def test_merge_with_unknown_into_branch_emits_e200() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "merge", "from": "main", "into": "ghost"}\n'

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E200"]


def test_merge_with_explicit_as_id_already_used_emits_e203() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m1"}\n'
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E203"]


def test_merge_auto_generates_id_when_as_omitted() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main"}\n'
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert len(state.branches["main"].commit_ids) == 2
    auto_id = state.branches["main"].commit_ids[-1]
    assert auto_id.startswith("_c")
