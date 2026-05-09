"""End-to-end tests for the state engine — multiple ops, error accumulation, import skipping."""

from tests.state._helpers import parse_and_apply


def test_empty_input_returns_empty_state_and_clean_report() -> None:
    # --- act --------------------------
    state, report = parse_and_apply("")

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branches == {}
    assert state.commits == {}


def test_engine_continues_past_semantic_errors() -> None:
    """Each op is attempted; semantic errors don't halt the engine."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "ghost", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "main"}\n'
        '{"op": "highlight", "commit": "c1"}\n'
    )

    # --- act --------------------------
    state, report = parse_and_apply(text)

    # --- assert -----------------------
    assert [(e.line, e.code) for e in report.errors] == [(2, "E200"), (4, "E202")]
    assert "c1" in state.commits
    assert state.commits["c1"].highlight is True


def test_import_op_is_skipped_during_state_apply() -> None:
    """Imports are shape-only at this layer; resolution comes later."""
    # --- arrange ----------------------
    text = '{"op": "import", "path": "./other.gitsvg.jsonl"}\n{"op": "branch", "name": "main"}\n'

    # --- act --------------------------
    state, report = parse_and_apply(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert "main" in state.branches


def test_full_realistic_scenario_with_branches_commits_merge_highlight() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main", "color": "#aabbcc"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "init"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "color": "#ccbbaa"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "feat work"}\n'
        '{"op": "commit", "branch": "feat", "id": "f2", "msg": "more feat"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "merge1"}\n'
        '{"op": "highlight", "commit": "merge1"}\n'
    )

    # --- act --------------------------
    state, report = parse_and_apply(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branch_order == ["main", "feat"]
    assert state.branches["main"].commit_ids == ["m1", "merge1"]
    assert state.branches["feat"].commit_ids == ["f1", "f2"]
    assert state.commits["merge1"].highlight is True
    assert set(state.commits["merge1"].parents) == {"m1", "f2"}
