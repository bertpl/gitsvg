"""Tests for the resolved-layout JSON serializer."""

from gitsvg.layout import compute_layout, layout_to_json
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops


def _layout_json(text: str) -> dict:
    """Parse JSONL → state → layout → serialized JSON dict."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    return layout_to_json(compute_layout(state))


def test_empty_input_emits_top_level_keys_with_empty_lists() -> None:
    # --- arrange / act ----------------
    payload = _layout_json("")

    # --- assert -----------------------
    assert set(payload.keys()) == {"grid", "branches", "commits", "arcs", "pull_requests"}
    assert payload["branches"] == []
    assert payload["commits"] == []
    assert payload["arcs"] == []
    assert payload["pull_requests"] == []


def test_linear_chain_emits_branch_and_commits() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "first"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "second"}\n'
    )

    # --- act --------------------------
    payload = _layout_json(jsonl)

    # --- assert -----------------------
    assert payload["grid"] == {"n_commits": 2, "n_branches": 1}
    assert len(payload["branches"]) == 1
    assert payload["branches"][0]["name"] == "main"
    assert payload["branches"][0]["branch_pos"] == 0
    assert [c["id"] for c in payload["commits"]] == ["c1", "c2"]
    assert payload["arcs"] == []


def test_branch_off_emits_branch_off_arc() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feature", "id": "f1", "msg": "y"}\n'
    )

    # --- act --------------------------
    payload = _layout_json(jsonl)

    # --- assert -----------------------
    arcs = payload["arcs"]
    assert len(arcs) == 1
    assert arcs[0]["kind"] == "branch_off"


def test_merge_emits_merge_arc() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feature", "id": "f1", "msg": "y"}\n'
        '{"op": "merge", "into": "main", "from": "feature", "as": "mg", "msg": "merge"}\n'
    )

    # --- act --------------------------
    payload = _layout_json(jsonl)

    # --- assert -----------------------
    merge_arcs = [a for a in payload["arcs"] if a["kind"] == "merge"]
    assert len(merge_arcs) == 1


def test_pull_request_emits_pull_request_geometry() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feature", "id": "f1", "msg": "y"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feature", "into": "main", "title": "ship it"}\n'
    )

    # --- act --------------------------
    payload = _layout_json(jsonl)

    # --- assert -----------------------
    assert len(payload["pull_requests"]) == 1
    pr = payload["pull_requests"][0]
    assert pr["id"] == "pr1"
    assert pr["title"] == "ship it"
    assert pr["from_branch_pos"] == 1
    assert pr["to_branch_pos"] == 0


def test_commits_serialized_as_list_not_dict() -> None:
    """The Layout dataclass keys commits by id; JSON serialization flattens to a list."""
    # --- arrange ----------------------
    jsonl = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'

    # --- act --------------------------
    payload = _layout_json(jsonl)

    # --- assert -----------------------
    assert isinstance(payload["commits"], list)
    assert payload["commits"][0]["id"] == "c1"


def test_grid_serialized_as_dict_with_slot_counts() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "y"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "z"}\n'
    )

    # --- act --------------------------
    payload = _layout_json(jsonl)

    # --- assert -----------------------
    assert payload["grid"] == {"n_commits": 3, "n_branches": 1}


def test_branch_carries_id_name_and_grid_positions() -> None:
    # --- arrange ----------------------
    jsonl = '{"op": "branch", "name": "main"}\n'

    # --- act --------------------------
    payload = _layout_json(jsonl)

    # --- assert -----------------------
    branch = payload["branches"][0]
    assert set(branch.keys()) == {"id", "name", "branch_pos", "segments", "start", "end", "tip_commit_id"}
    assert branch["id"] == "b0"
    assert branch["name"] == "main"
    assert branch["segments"] == [{"lane": 0, "start": 0, "end": 0}]
