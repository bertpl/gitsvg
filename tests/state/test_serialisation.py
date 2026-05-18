"""Tests for the resolved-state JSON serialiser."""

from gitsvg.state import state_to_json
from tests.state._helpers import build_state_from_jsonl


def test_empty_state_emits_empty_lists() -> None:
    # --- arrange / act ----------------
    state, report = build_state_from_jsonl("")
    payload = state_to_json(state)

    # --- assert -----------------------
    assert report.is_clean()
    assert payload == {"branches": [], "commits": [], "pull_requests": []}


def test_linear_chain_emits_chain_parents() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "first"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "second"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "third"}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- act --------------------------
    payload = state_to_json(state)

    # --- assert -----------------------
    assert report.is_clean()
    assert payload["branches"] == [{"name": "main", "head_commit_id": "c3"}]
    parents_by_id = {c["id"]: c["parents"] for c in payload["commits"]}
    assert parents_by_id == {"c1": [], "c2": ["c1"], "c3": ["c2"]}


def test_branch_off_first_commit_takes_rooted_on_commit_as_parent() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feature", "id": "f1", "msg": "y"}\n'
    )
    state, _report = build_state_from_jsonl(jsonl)

    # --- act --------------------------
    payload = state_to_json(state)

    # --- assert -----------------------
    feature = next(b for b in payload["branches"] if b["name"] == "feature")
    assert feature["head_commit_id"] == "f1"
    f1 = next(c for c in payload["commits"] if c["id"] == "f1")
    assert f1["branch"] == "feature"
    assert f1["parents"] == ["m1"]


def test_merge_emits_two_parents_into_then_from() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feature", "id": "f1", "msg": "y"}\n'
        '{"op": "merge", "into": "main", "from": "feature", "as": "mg", "msg": "merge"}\n'
    )
    state, _report = build_state_from_jsonl(jsonl)

    # --- act --------------------------
    payload = state_to_json(state)

    # --- assert -----------------------
    merge = next(c for c in payload["commits"] if c["id"] == "mg")
    assert merge["branch"] == "main"
    assert merge["parents"] == ["m1", "f1"]


def test_auto_hash_resolves_to_seven_char_hex() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x", "hash": "auto"}\n'
    )
    state, _report = build_state_from_jsonl(jsonl)

    # --- act --------------------------
    payload = state_to_json(state)

    # --- assert -----------------------
    c1 = payload["commits"][0]
    assert c1["hash"] is not None
    assert c1["hash"] != "auto"
    assert len(c1["hash"]) == 7
    assert all(ch in "0123456789abcdef" for ch in c1["hash"])


def test_commit_without_hash_emits_null() -> None:
    # --- arrange ----------------------
    jsonl = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
    state, _report = build_state_from_jsonl(jsonl)

    # --- act --------------------------
    payload = state_to_json(state)

    # --- assert -----------------------
    assert payload["commits"][0]["hash"] is None


def test_rebuild_pattern_emits_only_surviving_commits() -> None:
    """Remove-then-readd: the survivor with the same id appears once."""
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "first"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "second"}\n'
        '{"op": "remove", "commits": ["c2"]}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "redo"}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- act --------------------------
    payload = state_to_json(state)

    # --- assert -----------------------
    assert report.is_clean()
    ids = [c["id"] for c in payload["commits"]]
    assert ids.count("c2") == 1
    c2 = next(c for c in payload["commits"] if c["id"] == "c2")
    assert c2["msg"] == "redo"


def test_pull_request_emitted_with_from_into_and_title() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feature", "id": "f1", "msg": "y"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feature", "into": "main", "title": "ship it"}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- act --------------------------
    payload = state_to_json(state)

    # --- assert -----------------------
    assert report.is_clean()
    assert payload["pull_requests"] == [
        {"id": "pr1", "from_branch": "feature", "into_branch": "main", "title": "ship it"}
    ]


def test_pull_request_without_title_emits_null() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feature", "id": "f1", "msg": "y"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feature", "into": "main"}\n'
    )
    state, _report = build_state_from_jsonl(jsonl)

    # --- act --------------------------
    payload = state_to_json(state)

    # --- assert -----------------------
    assert payload["pull_requests"][0]["title"] is None


def test_branches_emitted_in_declaration_order() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "z_branch", "from_branch": "main"}\n'
        '{"op": "branch", "name": "a_branch", "from_branch": "main"}\n'
    )
    state, _report = build_state_from_jsonl(jsonl)

    # --- act --------------------------
    payload = state_to_json(state)

    # --- assert -----------------------
    assert [b["name"] for b in payload["branches"]] == ["main", "z_branch", "a_branch"]


def test_empty_branch_emits_null_head() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main"}\n'
    )
    state, _report = build_state_from_jsonl(jsonl)

    # --- act --------------------------
    payload = state_to_json(state)

    # --- assert -----------------------
    feature = next(b for b in payload["branches"] if b["name"] == "feature")
    assert feature["head_commit_id"] is None


def test_highlight_propagates_to_json() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "y"}\n'
        '{"op": "highlight", "commit": "c2"}\n'
    )
    state, _report = build_state_from_jsonl(jsonl)

    # --- act --------------------------
    payload = state_to_json(state)

    # --- assert -----------------------
    by_id = {c["id"]: c["highlight"] for c in payload["commits"]}
    assert by_id == {"c1": False, "c2": True}
