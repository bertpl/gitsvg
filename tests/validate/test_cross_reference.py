"""Tests for cross-reference validation (E400, E401)."""

from gitsvg.errors import ValidationReport
from gitsvg.validate import check_cross_reference
from tests.state._helpers import build_state_from_jsonl


# ==================================================================================================
#  Clean state — no cross-reference errors
# ==================================================================================================
def test_clean_state_produces_no_errors() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_commit": "c1"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)
    cross_ref_report = ValidationReport()
    check_cross_reference(state, cross_ref_report)

    # --- assert -----------------------
    assert report.is_clean()
    assert cross_ref_report.is_clean()


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
    state, report = build_state_from_jsonl(text)
    check_cross_reference(state, report)

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
    state, report = build_state_from_jsonl(text)
    check_cross_reference(state, report)

    # --- assert -----------------------
    assert [(e.line, e.code, e.field) for e in report.errors] == [(3, "E400", "from_branch")]


def test_branch_with_no_resolved_root_does_not_dangle() -> None:
    """A branch whose source was empty has rooted_on_commit=None; that's not dangling."""
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "branch", "name": "feat", "from_branch": "main"}\n'

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)
    check_cross_reference(state, report)

    # --- assert -----------------------
    assert report.is_clean()


# ==================================================================================================
#  E401 — dangling commit parent
# ==================================================================================================
def test_dangling_chain_parent_emits_e401() -> None:
    """Removing a mid-chain commit dangles its successor's stored chain parent."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "remove", "commits": ["c1"]}\n'
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)
    check_cross_reference(state, report)

    # --- assert -----------------------
    e401_errors = [e for e in report.errors if e.code == "E401"]
    assert len(e401_errors) == 1
    assert e401_errors[0].line == 3  # c2's declaration line
    assert e401_errors[0].field == "parents"


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
    state, report = build_state_from_jsonl(text)
    check_cross_reference(state, report)

    # --- assert -----------------------
    e401_errors = [e for e in report.errors if e.code == "E401"]
    assert len(e401_errors) == 1
    assert e401_errors[0].line == 5  # the merge op's line


# ==================================================================================================
#  Rebuild pattern — remove + re-add restores state
# ==================================================================================================
def test_rebuild_pattern_with_same_id_restores_state_and_passes() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_commit": "c1"}\n'
        '{"op": "remove", "commits": ["c1"]}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "rebuilt"}\n'
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)
    check_cross_reference(state, report)

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
    state, report = build_state_from_jsonl(text)
    check_cross_reference(state, report)

    # --- assert -----------------------
    assert report.is_clean()


# ==================================================================================================
#  Multiple dangling parents on one commit
# ==================================================================================================
def test_multiple_missing_parents_emit_one_error_per_dangling_parent() -> None:
    # --- arrange ----------------------
    # A merge commit carries two canonical parents (the into-side chain parent
    # `c1` and the merged-in tip `f1`). `feat` is rooted on `c0`, so removing
    # both `c1` and `f1` dangles exactly the two parents of `mg`.
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c0", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_commit": "c0"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "mg"}\n'
        '{"op": "remove", "commits": ["c1"]}\n'
        '{"op": "remove", "commits": ["f1"]}\n'
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)
    check_cross_reference(state, report)

    # --- assert -----------------------
    e401_errors = [e for e in report.errors if e.code == "E401"]
    assert len(e401_errors) == 2
    assert {e.field for e in e401_errors} == {"parents"}
    joined = " ".join(e.message for e in e401_errors)
    assert "c1" in joined
    assert "f1" in joined
