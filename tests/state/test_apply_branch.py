"""Tests for the `branch` op state-apply handler."""

from tests._jsonl import build_jsonl
from tests.state._helpers import build_state_from_jsonl


def test_first_branch_no_root_is_accepted() -> None:
    # --- act --------------------------
    state, report = build_state_from_jsonl(build_jsonl({"op": "branch", "name": "main"}))

    # --- assert -----------------------
    assert report.is_clean()
    assert "main" in state.branches
    assert state.branch_order == ["main"]


def test_branch_from_branch_resolves_root_to_source_tip() -> None:
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "branch", "name": "feat", "from_branch": "main"},
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branches["feat"].rooted_on_commit == "c1"


def test_branch_from_unborn_source_branch_has_no_root_commit() -> None:
    # Source `main` has no commits and no branch-off commit (unborn) → no ref
    # target to root on.
    # --- arrange ----------------------
    text = build_jsonl({"op": "branch", "name": "main"}, {"op": "branch", "name": "feat", "from_branch": "main"})

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branches["feat"].rooted_on_commit is None


def test_branch_from_empty_rooted_source_roots_on_its_branch_off_commit() -> None:
    # Source `feat` has no commits of its own but points at `c1` (branched off
    # main): a branch off `feat` roots on `c1`, where feat's ref points — not None.
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "branch", "name": "feat", "from_commit": "c1"},
        {"op": "branch", "name": "sub", "from_branch": "feat"},
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branches["sub"].rooted_on_commit == "c1"


def test_duplicate_branch_name_emits_e202() -> None:
    # --- arrange ----------------------
    text = build_jsonl({"op": "branch", "name": "main"}, {"op": "branch", "name": "main"})

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E202"]
    assert state.branches["main"].declaration_line == 1


def test_non_first_branch_without_root_emits_e204() -> None:
    # --- arrange ----------------------
    text = build_jsonl({"op": "branch", "name": "main"}, {"op": "branch", "name": "feat"})

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E204"]
    assert "feat" not in state.branches


def test_from_branch_pointing_at_undeclared_branch_emits_e200() -> None:
    # --- arrange ----------------------
    text = build_jsonl({"op": "branch", "name": "main"}, {"op": "branch", "name": "feat", "from_branch": "ghost"})

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E200"]


def test_from_commit_pointing_at_undeclared_commit_emits_e201() -> None:
    # --- arrange ----------------------
    text = build_jsonl({"op": "branch", "name": "main"}, {"op": "branch", "name": "feat", "from_commit": "ghost"})

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E201"]


def test_from_branch_when_name_is_actually_a_commit_id_hints_at_from_commit() -> None:
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "branch", "name": "feat", "from_branch": "c1"},
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert len(report.errors) == 1
    err = report.errors[0]
    assert err.code == "E200"
    assert "from_commit" in err.message


def test_branch_pos_override_is_stored_on_branch_state() -> None:
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"}, {"op": "branch", "name": "feat", "from_branch": "main", "branch_pos": 5}
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branches["feat"].branch_pos == 5


def test_branch_pos_omitted_leaves_branch_state_value_none() -> None:
    # --- arrange ----------------------
    text = build_jsonl({"op": "branch", "name": "main"})

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branches["main"].branch_pos is None
