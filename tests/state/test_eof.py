"""Tests for end-of-file cross-reference validation."""

from gitsvg.errors import ValidationReport
from gitsvg.state import check_end_of_file
from tests.state._helpers import run


# ==================================================================================================
#  Clean state — no EOF errors
# ==================================================================================================
def test_clean_state_produces_no_eof_errors() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_commit": "c1"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
    )

    # --- act --------------------------
    state, report = run(text)
    eof_report = ValidationReport()
    check_end_of_file(state, eof_report)

    # --- assert -----------------------
    assert report.is_clean()
    assert eof_report.is_clean()


# ==================================================================================================
#  E400 — dangling branch root
# ==================================================================================================
def test_dangling_branch_root_via_from_commit_emits_e400() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_commit": "c1"}\n'
        '{"op": "remove", "commits": ["c1"]}\n'
    )

    # --- act --------------------------
    state, report = run(text)
    check_end_of_file(state, report)

    # --- assert -----------------------
    assert [(e.line, e.code, e.field) for e in report.errors] == [(3, "E400", "from_commit")]


def test_dangling_branch_root_via_from_branch_emits_e400() -> None:
    """from_branch resolves to the source branch's tip; if that tip is later removed the root dangles."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "remove", "commits": ["c1"]}\n'
    )

    # --- act --------------------------
    state, report = run(text)
    check_end_of_file(state, report)

    # --- assert -----------------------
    assert [(e.line, e.code, e.field) for e in report.errors] == [(3, "E400", "from_branch")]


def test_branch_with_no_resolved_root_does_not_dangle() -> None:
    """A branch whose source was empty has rooted_on_commit=None; that's not dangling."""
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "branch", "name": "feat", "from_branch": "main"}\n'

    # --- act --------------------------
    state, report = run(text)
    check_end_of_file(state, report)

    # --- assert -----------------------
    assert report.is_clean()


# ==================================================================================================
#  E401 — dangling commit parent
# ==================================================================================================
def test_dangling_explicit_parent_emits_e401() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x", "parents": ["c1"]}\n'
        '{"op": "remove", "commits": ["c1"]}\n'
    )

    # --- act --------------------------
    state, report = run(text)
    check_end_of_file(state, report)

    # --- assert -----------------------
    e401_errors = [e for e in report.errors if e.code == "E401"]
    assert len(e401_errors) == 1
    assert e401_errors[0].line == 4
    assert e401_errors[0].field == "parents.0"


def test_dangling_merge_parent_emits_e401() -> None:
    """Merge auto-generates parents from from/into tips; removing a tip dangles the merge."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "merge1"}\n'
        '{"op": "remove", "commits": ["f1"]}\n'
    )

    # --- act --------------------------
    state, report = run(text)
    check_end_of_file(state, report)

    # --- assert -----------------------
    e401_errors = [e for e in report.errors if e.code == "E401"]
    assert len(e401_errors) == 1
    assert e401_errors[0].line == 5  # the merge op's line


# ==================================================================================================
#  Rebuild pattern — remove + re-add restores state
# ==================================================================================================
def test_rebuild_pattern_with_same_id_restores_state_and_passes_eof() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_commit": "c1"}\n'
        '{"op": "remove", "commits": ["c1"]}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "rebuilt"}\n'
    )

    # --- act --------------------------
    state, report = run(text)
    check_end_of_file(state, report)

    # --- assert -----------------------
    assert report.is_clean()


def test_rebuild_pattern_for_branch_remove_then_redeclare() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_commit": "c1"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "remove", "branches": ["feat"]}\n'
        '{"op": "branch", "name": "feat", "from_commit": "c1"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
    )

    # --- act --------------------------
    state, report = run(text)
    check_end_of_file(state, report)

    # --- assert -----------------------
    assert report.is_clean()


# ==================================================================================================
#  Multiple dangling parents on one commit
# ==================================================================================================
def test_multiple_missing_parents_emit_one_error_per_dangling_parent() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x", "parents": ["c1", "c2"]}\n'
        '{"op": "remove", "commits": ["c1"]}\n'
        '{"op": "remove", "commits": ["c2"]}\n'
    )

    # --- act --------------------------
    state, report = run(text)
    check_end_of_file(state, report)

    # --- assert -----------------------
    e401_errors = [e for e in report.errors if e.code == "E401"]
    assert len(e401_errors) == 2
    assert sorted(e.field for e in e401_errors) == ["parents.0", "parents.1"]
