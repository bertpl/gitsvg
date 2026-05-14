"""Tests for the `State` container helpers."""

from gitsvg.state import BranchState, State


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
