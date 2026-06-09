"""Tests for the `pull_request` apply handler and the validation rules
it enforces together with `remove` and `merge`."""

from tests.state._helpers import build_state_from_jsonl


# ==================================================================================================
#  Happy path — opens a PR, populates state.pull_requests
# ==================================================================================================
def test_explicit_id_opens_pr() -> None:
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main", "title": "WIP"}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.has_pull_request("pr1")
    pr = state.pull_requests["pr1"]
    assert pr.from_branch == "feat"
    assert pr.into_branch == "main"
    assert pr.title == "WIP"


def test_auto_id_generated_when_omitted() -> None:
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "pull_request", "from": "feat", "into": "main"}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    assert report.is_clean()
    assert "_pr1" in state.pull_requests
    assert state.pull_requests["_pr1"].from_branch == "feat"


def test_auto_id_increments_across_multiple_prs() -> None:
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat1", "from_branch": "main"}\n'
        '{"op": "branch", "name": "feat2", "from_branch": "main"}\n'
        '{"op": "pull_request", "from": "feat1", "into": "main"}\n'
        '{"op": "pull_request", "from": "feat2", "into": "main"}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    assert report.is_clean()
    assert set(state.pull_requests.keys()) == {"_pr1", "_pr2"}


# ==================================================================================================
#  Rule 1 — `from` == `into` rejected (E210)
# ==================================================================================================
def test_from_equals_into_rejected() -> None:
    # --- arrange / act ----------------
    jsonl = '{"op": "branch", "name": "main"}\n{"op": "pull_request", "from": "main", "into": "main"}\n'
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    assert not report.is_clean()
    codes = {e.code for e in report.errors}
    assert "E210" in codes
    assert state.pull_requests == {}


# ==================================================================================================
#  Rule 2 — unknown branch references rejected (E200)
# ==================================================================================================
def test_unknown_from_branch_rejected() -> None:
    # --- arrange / act ----------------
    jsonl = '{"op": "branch", "name": "main"}\n{"op": "pull_request", "from": "ghost", "into": "main"}\n'
    _state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    assert not report.is_clean()
    errors_with_e200 = [e for e in report.errors if e.code == "E200"]
    assert errors_with_e200
    assert errors_with_e200[0].field == "from"


def test_unknown_into_branch_rejected() -> None:
    # --- arrange / act ----------------
    jsonl = '{"op": "branch", "name": "main"}\n{"op": "pull_request", "from": "main", "into": "ghost"}\n'
    _state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    errors_with_e200 = [e for e in report.errors if e.code == "E200"]
    assert errors_with_e200
    assert errors_with_e200[0].field == "into"


# ==================================================================================================
#  Rule 3 — duplicate (from, into) pair rejected (E212)
# ==================================================================================================
def test_duplicate_open_pr_for_same_pair_rejected() -> None:
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"}\n'
        '{"op": "pull_request", "id": "pr2", "from": "feat", "into": "main"}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    codes = {e.code for e in report.errors}
    assert "E212" in codes
    # First PR survived; second one rejected.
    assert "pr1" in state.pull_requests
    assert "pr2" not in state.pull_requests


def test_duplicate_id_rejected() -> None:
    """E211 — explicit `id` collides with an existing open PR."""
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat1", "from_branch": "main"}\n'
        '{"op": "branch", "name": "feat2", "from_branch": "main"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat1", "into": "main"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat2", "into": "main"}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    codes = {e.code for e in report.errors}
    assert "E211" in codes
    # Original `pr1` survives unchanged.
    assert state.pull_requests["pr1"].from_branch == "feat1"


# ==================================================================================================
#  Rule 4 — remove branch blocked by open PR (E214)
# ==================================================================================================
def test_remove_branch_blocked_by_open_pr_as_from() -> None:
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"}\n'
        '{"op": "remove", "branches": ["feat"]}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    codes = {e.code for e in report.errors}
    assert "E214" in codes
    # The branch and the PR are both still present.
    assert state.has_branch("feat")
    assert state.has_pull_request("pr1")


def test_remove_branch_blocked_by_open_pr_as_into() -> None:
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"}\n'
        '{"op": "remove", "branches": ["main"]}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    codes = {e.code for e in report.errors}
    assert "E214" in codes
    assert state.has_branch("main")


def test_remove_branch_succeeds_after_pr_closed() -> None:
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"}\n'
        '{"op": "remove", "pull_requests": ["pr1"]}\n'
        '{"op": "remove", "branches": ["feat"]}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    assert report.is_clean()
    assert not state.has_branch("feat")
    assert not state.has_pull_request("pr1")


# ==================================================================================================
#  Rule 5 — merge blocked by matching open PR (E213)
# ==================================================================================================
def test_merge_blocked_by_matching_open_pr() -> None:
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "first"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "wip"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"}\n'
        '{"op": "merge", "from": "feat", "into": "main"}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    codes = {e.code for e in report.errors}
    assert "E213" in codes
    # Merge did not produce a new commit on main beyond m1.
    assert state.branches["main"].commit_ids == ["m1"]


def test_merge_succeeds_after_matching_pr_closed() -> None:
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "first"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "wip"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"}\n'
        '{"op": "remove", "pull_requests": ["pr1"]}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "merged"}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.has_commit("merged")
    assert "merged" in state.branches["main"].commit_ids


def test_merge_with_different_pair_not_blocked() -> None:
    """An open PR on one pair doesn't block merges on a different pair."""
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "first"}\n'
        '{"op": "branch", "name": "feat1", "from_branch": "main"}\n'
        '{"op": "branch", "name": "feat2", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat2", "id": "f2", "msg": "wip"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat1", "into": "main"}\n'
        '{"op": "merge", "from": "feat2", "into": "main", "as": "m2"}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.has_commit("m2")
    assert state.has_pull_request("pr1")
