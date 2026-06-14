"""Tests for the `commit` op state-apply handler — including auto-id generation,
parents validation, id uniqueness, and the seven `replaces:` rules."""

import pytest

from tests._jsonl import build_jsonl
from tests.state._helpers import build_state_from_jsonl


# ==================================================================================================
#  Happy path
# ==================================================================================================
def test_commit_appends_to_branch() -> None:
    # --- arrange ----------------------
    text = build_jsonl({"op": "branch", "name": "main"}, {"op": "commit", "branch": "main", "id": "c1", "msg": "x"})

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branches["main"].commit_ids == ["c1"]
    assert state.commits["c1"].branch == "main"


def test_auto_id_generation_uses_underscore_c_n_namespace() -> None:
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "first"},
        {"op": "commit", "branch": "main", "msg": "auto"},
        {"op": "commit", "branch": "main", "msg": "auto"},
    )

    # --- act --------------------------
    state, _ = build_state_from_jsonl(text)

    # --- assert -----------------------
    # User-supplied `c1` does not collide with the `_c<N>` auto-id namespace.
    assert state.branches["main"].commit_ids == ["c1", "_c1", "_c2"]


def test_auto_id_skips_already_used_underscore_c_n_ids() -> None:
    """An explicit `_c2` (rare; reserved-pattern but legal) makes auto-id pick `_c1` then `_c3`."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "_c2", "msg": "x"},
        {"op": "commit", "branch": "main", "msg": "x"},
        {"op": "commit", "branch": "main", "msg": "x"},
    )

    # --- act --------------------------
    state, _ = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert state.branches["main"].commit_ids == ["_c2", "_c1", "_c3"]


# ==================================================================================================
#  Branch / parents / id-uniqueness errors
# ==================================================================================================
def test_commit_on_undeclared_branch_emits_e200() -> None:
    # --- act --------------------------
    _, report = build_state_from_jsonl(build_jsonl({"op": "commit", "branch": "main", "msg": "x"}))

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E200"]


def test_duplicate_commit_id_emits_e203() -> None:
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "first"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "second"},
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E203"]


# ==================================================================================================
#  replaces: rules — one test per rule
# ==================================================================================================
def test_replaces_rule_1_undefined_commit_emits_e201() -> None:
    """Rule 1: every id in replaces must exist."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"}, {"op": "commit", "branch": "main", "msg": "x", "replaces": ["ghost"]}
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E201"]


def test_replaces_rule_2_cross_branch_emits_e205() -> None:
    """Rule 2: replaced commits must be on the new commit's branch."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "m1", "msg": "x"},
        {"op": "branch", "name": "feat", "from_branch": "main"},
        {"op": "commit", "branch": "feat", "id": "f1", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "m2", "msg": "squash", "replaces": ["m1", "f1"]},
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E205"]


def test_replaces_rule_3_non_contiguous_tail_emits_e206() -> None:
    """Rule 3: replaced commits must form a contiguous range at the tail."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c2", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c3", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c4", "msg": "squash", "replaces": ["c1", "c3"]},
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E206"]


def test_replaces_rule_4_other_branch_rooted_emits_e207() -> None:
    """Rule 4: no other branch rooted on a replaced commit."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "branch", "name": "feat", "from_commit": "c1"},
        {"op": "commit", "branch": "main", "id": "c2", "msg": "squash", "replaces": ["c1"]},
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E207"]


def test_replaces_rule_5_external_parents_emits_e208() -> None:
    """Rule 5: an external commit's canonical parents may not reference a replaced commit.

    A merge into `feat` records `main`'s tip (`c1`) as a parent of `mg`;
    squashing `c1` on `main` then leaves `mg` pointing at a replaced commit.
    `feat` is rooted on `c0`, not `c1`, so rule 4 (E207) does not pre-empt
    rule 5 — this isolates the E208 path.
    """
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c0", "msg": "x"},
        {"op": "branch", "name": "feat", "from_commit": "c0"},
        {"op": "commit", "branch": "feat", "id": "f0", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "merge", "from": "main", "into": "feat", "as": "mg"},
        {"op": "commit", "branch": "main", "id": "c2", "msg": "squash", "replaces": ["c1"]},
    )

    # --- act --------------------------
    _, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E208"]


def test_replaces_happy_path_atomically_squashes_tail() -> None:
    """A valid squash removes the listed commits and adds the new one."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c2", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c3", "msg": "squashed", "replaces": ["c1", "c2"]},
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branches["main"].commit_ids == ["c3"]
    assert "c1" not in state.commits
    assert "c2" not in state.commits


def test_replaces_can_reuse_a_vacated_id() -> None:
    """The new commit may reuse an id that's being vacated by replaces."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "renamed", "replaces": ["c1"]},
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.branches["main"].commit_ids == ["c1"]
    assert state.commits["c1"].msg == "renamed"


# ==================================================================================================
#  Highlight via commit field
# ==================================================================================================
@pytest.mark.parametrize(("highlight_value", "expected"), [(True, True), (False, False), (None, False)])
def test_highlight_field_propagates_to_commit_state(highlight_value: bool | None, expected: bool) -> None:
    # --- arrange ----------------------
    extra = {"highlight": highlight_value} if highlight_value is not None else {}
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x", **extra},
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.commits["c1"].highlight is expected


# ==================================================================================================
#  Gap field
# ==================================================================================================
@pytest.mark.parametrize(("gap_value", "expected"), [(2, 2), (0, 0), (None, 0)])
def test_gap_field_propagates_to_commit_state(gap_value: int | None, expected: int) -> None:
    # --- arrange ----------------------
    extra = {"gap": gap_value} if gap_value is not None else {}
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x", **extra},
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.commits["c1"].gap == expected


# ==================================================================================================
#  Gap inheritance for replaces commits
# ==================================================================================================
def test_replaces_commit_inherits_earliest_replaced_gap_when_op_gap_unset() -> None:
    """A `replaces:` commit without `op.gap` inherits the earliest replaced
    commit's gap, preserving any visual breathing room the original chain had."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c2", "msg": "x", "gap": 2},
        {"op": "commit", "branch": "main", "id": "c3", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "csquash", "msg": "squash", "replaces": ["c2", "c3"]},
    )

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    # c2 was the earliest replaced commit; its gap was 2.
    assert state.commits["csquash"].gap == 2


def test_replaces_commit_op_gap_overrides_inheritance() -> None:
    """An explicit `op.gap` on a `replaces:` commit wins over inheritance."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c2", "msg": "x", "gap": 5},
        {"op": "commit", "branch": "main", "id": "csquash", "msg": "squash", "replaces": ["c2"], "gap": 1},
    )

    # --- act --------------------------
    state, _ = build_state_from_jsonl(text)

    # --- assert -----------------------
    # Explicit gap=1 on csquash overrides the inherited gap=5 from c2.
    assert state.commits["csquash"].gap == 1


def test_replaces_commit_inherits_zero_when_replaced_had_no_gap() -> None:
    """The common case: replaced commits had gap=0; squash inherits 0."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c2", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "csquash", "msg": "squash", "replaces": ["c2"]},
    )

    # --- act --------------------------
    state, _ = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert state.commits["csquash"].gap == 0


def test_replaces_with_unordered_list_picks_earliest_in_branch_order() -> None:
    """The `replaces:` list order is user-controlled; inheritance picks the
    earliest replaced commit in branch.commit_ids order, not list order."""
    # --- arrange ----------------------
    text = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
        {"op": "commit", "branch": "main", "id": "c2", "msg": "x", "gap": 3},
        {"op": "commit", "branch": "main", "id": "c3", "msg": "x", "gap": 7},
        {"op": "commit", "branch": "main", "id": "csquash", "msg": "squash", "replaces": ["c3", "c2"]},
    )

    # --- act --------------------------
    state, _ = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert state.commits["csquash"].gap == 3
