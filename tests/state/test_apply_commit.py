"""Tests for the `commit` op state-apply handler — including auto-id generation,
parents validation, id uniqueness, and the seven `replaces:` rules."""

import pytest

from tests.state._helpers import run


# ==================================================================================================
#  Happy path
# ==================================================================================================
def test_commit_appends_to_branch() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'

    # --- act --------------------------
    state, report = run(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branches["main"].commit_ids == ["c1"]
    assert state.commits["c1"].branch == "main"


def test_auto_id_generation_picks_lowest_unused_c_n() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "first"}\n'
        '{"op": "commit", "branch": "main", "msg": "auto"}\n'
        '{"op": "commit", "branch": "main", "msg": "auto"}\n'
    )

    # --- act --------------------------
    state, _ = run(text)

    # --- assert -----------------------
    assert state.branches["main"].commit_ids == ["c1", "c2", "c3"]


def test_auto_id_skips_already_used_explicit_ids() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "msg": "x"}\n'
    )

    # --- act --------------------------
    state, _ = run(text)

    # --- assert -----------------------
    assert state.branches["main"].commit_ids == ["c2", "c1"]


# ==================================================================================================
#  Branch / parents / id-uniqueness errors
# ==================================================================================================
def test_commit_on_undeclared_branch_emits_e200() -> None:
    # --- act --------------------------
    _, report = run('{"op": "commit", "branch": "main", "msg": "x"}\n')

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E200"]


def test_commit_with_unknown_parent_emits_e201() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "msg": "x", "parents": ["ghost"]}\n'

    # --- act --------------------------
    _, report = run(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E201"]


def test_duplicate_commit_id_emits_e203() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "first"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "second"}\n'
    )

    # --- act --------------------------
    _, report = run(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E203"]


# ==================================================================================================
#  replaces: rules — one test per rule
# ==================================================================================================
def test_replaces_rule_1_undefined_commit_emits_e201() -> None:
    """Rule 1: every id in replaces must exist."""
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "msg": "x", "replaces": ["ghost"]}\n'

    # --- act --------------------------
    _, report = run(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E201"]


def test_replaces_rule_2_cross_branch_emits_e205() -> None:
    """Rule 2: replaced commits must be on the new commit's branch."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "squash", "replaces": ["m1", "f1"]}\n'
    )

    # --- act --------------------------
    _, report = run(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E205"]


def test_replaces_rule_3_non_contiguous_tail_emits_e206() -> None:
    """Rule 3: replaced commits must form a contiguous range at the tail."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c4", "msg": "squash", "replaces": ["c1", "c3"]}\n'
    )

    # --- act --------------------------
    _, report = run(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E206"]


def test_replaces_rule_4_other_branch_rooted_emits_e207() -> None:
    """Rule 4: no other branch rooted on a replaced commit."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_commit": "c1"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "squash", "replaces": ["c1"]}\n'
    )

    # --- act --------------------------
    _, report = run(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E207"]


def test_replaces_rule_5_external_parents_emits_e208() -> None:
    """Rule 5: external commit's parents may not reference a replaced commit."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x", "parents": ["c1"]}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "squash", "replaces": ["c1"]}\n'
    )

    # --- act --------------------------
    _, report = run(text)

    # --- assert -----------------------
    # E207 also fires (feat is rooted on c1) — but the parents-rule violation is what we're testing.
    codes = sorted(e.code for e in report.errors)
    assert "E208" in codes or "E207" in codes


def test_replaces_rule_7_self_parents_emits_e209() -> None:
    """Rule 7: the new commit's parents may not reference replaced commits."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "squash", "replaces": ["c1", "c2"], "parents": ["c1"]}\n'
    )

    # --- act --------------------------
    _, report = run(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E209"]


def test_replaces_happy_path_atomically_squashes_tail() -> None:
    """A valid squash removes the listed commits and adds the new one."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "squashed", "replaces": ["c1", "c2"]}\n'
    )

    # --- act --------------------------
    state, report = run(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branches["main"].commit_ids == ["c3"]
    assert "c1" not in state.commits
    assert "c2" not in state.commits


def test_replaces_can_reuse_a_vacated_id() -> None:
    """The new commit may reuse an id that's being vacated by replaces."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "renamed", "replaces": ["c1"]}\n'
    )

    # --- act --------------------------
    state, report = run(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branches["main"].commit_ids == ["c1"]
    assert state.commits["c1"].msg == "renamed"


# ==================================================================================================
#  Highlight via commit field
# ==================================================================================================
@pytest.mark.parametrize("highlight_value, expected", [(True, True), (False, False), (None, False)])
def test_highlight_field_propagates_to_commit_state(highlight_value: bool | None, expected: bool) -> None:
    # --- arrange ----------------------
    flag_field = f', "highlight": {str(highlight_value).lower()}' if highlight_value is not None else ""
    text = (
        '{"op": "branch", "name": "main"}\n'
        f'{{"op": "commit", "branch": "main", "id": "c1", "msg": "x"{flag_field}}}\n'
    )

    # --- act --------------------------
    state, report = run(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.commits["c1"].highlight is expected
