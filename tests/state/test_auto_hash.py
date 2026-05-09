"""Tests for `hash: "auto"` deterministic generation.

Covers the pure `compute_auto_hash` and `effective_parent_ids` helpers
plus end-to-end behaviour through the state-apply pipeline (commits,
merges, replaces, fork branches, and the rebase-style chain
propagation pattern).
"""

import re

import pytest

from gitsvg.state._auto_hash import compute_auto_hash, effective_parent_ids
from tests.state._helpers import build_state_from_jsonl


# ==================================================================================================
#  Pure compute_auto_hash function
# ==================================================================================================
def test_compute_auto_hash_is_deterministic() -> None:
    # --- act --------------------------
    a = compute_auto_hash("c1", ["p1"])
    b = compute_auto_hash("c1", ["p1"])

    # --- assert -----------------------
    assert a == b


def test_compute_auto_hash_is_seven_lowercase_hex_chars() -> None:
    # --- act --------------------------
    h = compute_auto_hash("c1", ["p1"])

    # --- assert -----------------------
    assert re.fullmatch(r"[0-9a-f]{7}", h) is not None


def test_compute_auto_hash_changes_when_id_changes() -> None:
    # --- arrange / act ----------------
    h1 = compute_auto_hash("c1", ["p1"])
    h2 = compute_auto_hash("c2", ["p1"])

    # --- assert -----------------------
    assert h1 != h2


def test_compute_auto_hash_changes_when_parent_changes() -> None:
    # --- arrange / act ----------------
    h1 = compute_auto_hash("c1", ["p1"])
    h2 = compute_auto_hash("c1", ["p2"])

    # --- assert -----------------------
    assert h1 != h2


def test_compute_auto_hash_is_insensitive_to_parent_order() -> None:
    """Sorting the parent list before hashing means a merge of `from=A into=B`
    and a (hypothetical) merge of `from=B into=A` yield the same hash for the
    same merge-commit id, since the parent *set* is identical."""
    # --- act --------------------------
    a = compute_auto_hash("m1", ["pA", "pB"])
    b = compute_auto_hash("m1", ["pB", "pA"])

    # --- assert -----------------------
    assert a == b


def test_compute_auto_hash_distinguishes_no_parents_from_one_parent() -> None:
    """A root commit (no parents) and a child commit (one parent) with the
    same id must produce different hashes — otherwise rebase semantics
    can't distinguish a commit at the chain root from one further down."""
    # --- arrange / act ----------------
    h_root = compute_auto_hash("c1", [])
    h_child = compute_auto_hash("c1", ["p1"])

    # --- assert -----------------------
    assert h_root != h_child


# ==================================================================================================
#  End-to-end: hash="auto" resolution on commit ops
# ==================================================================================================
def test_root_commit_with_auto_hash_resolves_to_seven_hex_chars() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "hash": "auto"}\n'

    # --- act --------------------------
    state, report = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert report.is_clean()
    resolved = state.commits["c1"].hash
    assert resolved is not None
    assert resolved != "auto"
    assert re.fullmatch(r"[0-9a-f]{7}", resolved) is not None


def test_explicit_hash_is_left_alone() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "hash": "deadbef"}\n'

    # --- act --------------------------
    state, _ = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert state.commits["c1"].hash == "deadbef"


def test_no_hash_field_stays_none() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'

    # --- act --------------------------
    state, _ = build_state_from_jsonl(text)

    # --- assert -----------------------
    assert state.commits["c1"].hash is None


def test_chain_uses_implicit_chain_parent() -> None:
    """A second commit on a branch hashes id + previous-commit-id."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "hash": "auto"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "hash": "auto"}\n'
    )

    # --- act --------------------------
    state, _ = build_state_from_jsonl(text)

    # --- assert -----------------------
    expected_c2 = compute_auto_hash("c2", ["c1"])
    assert state.commits["c2"].hash == expected_c2


def test_first_commit_on_fork_branch_uses_rooted_on_commit() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "hash": "auto"}\n'
    )

    # --- act --------------------------
    state, _ = build_state_from_jsonl(text)

    # --- assert -----------------------
    expected = compute_auto_hash("f1", ["m1"])
    assert state.commits["f1"].hash == expected


def test_explicit_parents_override_implicit_chain_parent() -> None:
    """When a commit op sets `parents:`, those are the immediate parents
    for hash purposes — the chain parent on the branch is not added."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "hash": "auto", "parents": ["c1"]}\n'
    )

    # --- act --------------------------
    state, _ = build_state_from_jsonl(text)

    # --- assert -----------------------
    # Chain parent would be c2 (main's tip when feat was forked), but the explicit
    # parents=["c1"] takes over.
    expected = compute_auto_hash("f1", ["c1"])
    assert state.commits["f1"].hash == expected


# ==================================================================================================
#  End-to-end: hash="auto" resolution on merge ops
# ==================================================================================================
def test_merge_with_auto_hash_uses_both_parent_tips() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m2", "hash": "auto"}\n'
    )

    # --- act --------------------------
    state, _ = build_state_from_jsonl(text)

    # --- assert -----------------------
    # Both tips were [m1, f1] at merge time. Sorted before hashing.
    expected = compute_auto_hash("m2", ["m1", "f1"])
    assert state.commits["m2"].hash == expected


# ==================================================================================================
#  End-to-end: hash="auto" + replaces (squash)
# ==================================================================================================
def test_replaces_commit_uses_post_removal_chain_parent() -> None:
    """A `replaces:` commit's chain parent is the commit before the *first*
    replaced commit — because removals happen before the new commit is added."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c4", "msg": "squash", '
        '"hash": "auto", "replaces": ["c2", "c3"]}\n'
    )

    # --- act --------------------------
    state, _ = build_state_from_jsonl(text)

    # --- assert -----------------------
    # After removing c2 and c3, the branch is [c1] when c4 lands.
    # c4's chain parent is therefore c1.
    expected = compute_auto_hash("c4", ["c1"])
    assert state.commits["c4"].hash == expected


# ==================================================================================================
#  Chain propagation — the rebase-id-rename pattern
# ==================================================================================================
def test_renaming_an_upstream_id_changes_downstream_auto_hashes() -> None:
    """The user's idiomatic 'rebase' is remove + re-declare with a new id.
    Downstream commits whose chain parent now points at the new id end up
    with new auto-hashes, mirroring git's rebase semantics."""
    # --- arrange ----------------------
    # Scenario A: c1 → c2 → c3 (all auto)
    text_a = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "hash": "auto"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "hash": "auto"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "hash": "auto"}\n'
    )

    # Scenario B: same as A but c2 has been "rebased" — renamed to c2_prime
    text_b = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "hash": "auto"}\n'
        '{"op": "commit", "branch": "main", "id": "c2_prime", "hash": "auto"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "hash": "auto"}\n'
    )

    # --- act --------------------------
    state_a, _ = build_state_from_jsonl(text_a)
    state_b, _ = build_state_from_jsonl(text_b)

    # --- assert -----------------------
    # c1 unchanged across scenarios.
    assert state_a.commits["c1"].hash == state_b.commits["c1"].hash
    # c3 has the same id in both but a different chain parent → different hash.
    assert state_a.commits["c3"].hash != state_b.commits["c3"].hash


# ==================================================================================================
#  effective_parent_ids helper
# ==================================================================================================
def test_effective_parent_ids_for_root_commit_is_empty() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    state, _ = build_state_from_jsonl(text)

    # --- act --------------------------
    parents = effective_parent_ids(state, "c1", "main")

    # --- assert -----------------------
    assert parents == []


def test_effective_parent_ids_for_chain_commit() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
    )
    state, _ = build_state_from_jsonl(text)

    # --- act --------------------------
    parents = effective_parent_ids(state, "c2", "main")

    # --- assert -----------------------
    assert parents == ["c1"]


def test_effective_parent_ids_prefers_explicit_parents() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x", "parents": ["c1"]}\n'
    )
    state, _ = build_state_from_jsonl(text)

    # --- act --------------------------
    parents = effective_parent_ids(state, "c2", "main")

    # --- assert -----------------------
    # Explicit parents wins (here it happens to coincide with chain parent,
    # but the helper is still returning the explicit list, not deriving from chain).
    assert parents == ["c1"]


# ==================================================================================================
#  Schema-level acceptance for hash="auto" on merge op
# ==================================================================================================
@pytest.mark.parametrize(
    "raw",
    [
        {"op": "merge", "from": "feat", "into": "main", "hash": "auto"},
        {"op": "merge", "from": "feat", "into": "main", "hash": "abc1234"},
    ],
)
def test_merge_op_accepts_hash_field(raw: dict) -> None:
    """Just a smoke test that the schema-level layer accepts `hash:` on merge."""
    # --- act --------------------------
    from gitsvg.file_format.ops import OP_ADAPTER

    op = OP_ADAPTER.validate_python(raw)

    # --- assert -----------------------
    assert op.op == "merge"
    assert op.hash == raw["hash"]
