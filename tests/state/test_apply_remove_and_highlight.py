"""Tests for the `remove`, `highlight`, and `canvas` op state-apply handlers."""

from tests.state._helpers import build_state_from_jsonl


# ==================================================================================================
#  remove
# ==================================================================================================
def test_remove_commits_drops_them_from_state() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "remove", "commits": ["c1"]}\n'
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert "c1" not in state.commits
    assert state.branches["main"].commit_ids == ["c2"]


def test_remove_branch_cascades_to_its_commits() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "commit", "branch": "feat", "id": "f2", "msg": "x"}\n'
        '{"op": "remove", "branches": ["feat"]}\n'
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert "feat" not in state.branches
    assert "f1" not in state.commits
    assert "f2" not in state.commits


def test_remove_unknown_commit_emits_e201() -> None:
    # --- act --------------------------
    _, report = build_state_from_jsonl('{"op": "branch", "name": "main"}\n{"op": "remove", "commits": ["ghost"]}\n')

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E201"]


def test_remove_unknown_branch_emits_e200() -> None:
    # --- act --------------------------
    _, report = build_state_from_jsonl('{"op": "branch", "name": "main"}\n{"op": "remove", "branches": ["ghost"]}\n')

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E200"]


def test_remove_then_redeclare_branch_with_same_name_works() -> None:
    """The remove + redeclare pattern should leave a clean state."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "remove", "branches": ["feat"]}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert "feat" in state.branches


# ==================================================================================================
#  highlight
# ==================================================================================================
def test_highlight_existing_commit_sets_flag() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "highlight", "commit": "c1"}\n'
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.commits["c1"].highlight is True


def test_highlight_unknown_commit_emits_e201() -> None:
    # --- act --------------------------
    _, report = build_state_from_jsonl('{"op": "branch", "name": "main"}\n{"op": "highlight", "commit": "ghost"}\n')

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E201"]


# ==================================================================================================
#  grid
# ==================================================================================================
def test_grid_op_pins_dimensions_in_state() -> None:
    # --- arrange ----------------------
    text = '{"op": "grid", "n_commits": 5, "n_branches": 2}\n'

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.grid is not None
    assert state.grid.n_commits == 5
    assert state.grid.n_branches == 2


def test_grid_last_op_wins() -> None:
    # --- arrange ----------------------
    text = '{"op": "grid", "n_commits": 5}\n{"op": "grid", "n_commits": 10}\n'

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.grid is not None
    assert state.grid.n_commits == 10
