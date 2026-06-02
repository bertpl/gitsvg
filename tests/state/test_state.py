"""Tests for the `State` container helpers."""

from gitsvg.state import BranchState, State
from tests.state._helpers import build_state_from_jsonl


def test_new_state_is_empty() -> None:
    # --- act --------------------------
    state = State()

    # --- assert -----------------------
    assert state.branches == {}
    assert state.commits == {}
    assert state.branch_order == []
    assert state.grid is None
    assert state.is_first_branch() is True


def test_is_first_branch_false_after_first_branch_added() -> None:
    # --- arrange ----------------------
    state = State()
    state.branches["main"] = BranchState(id="b0", name="main")

    # --- act / assert -----------------
    assert state.is_first_branch() is False


def test_branch_tip_returns_none_for_empty_branch() -> None:
    # --- arrange ----------------------
    state = State()
    state.branches["main"] = BranchState(id="b0", name="main")

    # --- act / assert -----------------
    assert state.branch_tip("main") is None


def test_branch_tip_returns_last_commit_id() -> None:
    # --- arrange ----------------------
    state = State()
    state.branches["main"] = BranchState(id="b0", name="main", commit_ids=["c1", "c2", "c3"])

    # --- act / assert -----------------
    assert state.branch_tip("main") == "c3"


def test_branch_tip_returns_none_for_unknown_branch() -> None:
    # --- arrange ----------------------
    state = State()

    # --- act / assert -----------------
    assert state.branch_tip("ghost") is None


def test_remove_commit_drops_from_commits_and_branch() -> None:
    # --- arrange ----------------------
    state, _report = build_state_from_jsonl(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "a"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "b"}\n'
    )

    # --- act --------------------------
    state.remove_commit("c1")

    # --- assert -----------------------
    assert "c1" not in state.commits
    assert state.branches["main"].commit_ids == ["c2"]


def test_remove_commit_is_noop_for_absent_id() -> None:
    # --- arrange ----------------------
    state, _report = build_state_from_jsonl('{"op": "branch", "name": "main"}\n')

    # --- act --------------------------
    state.remove_commit("does-not-exist")

    # --- assert -----------------------
    assert state.commits == {}
