"""Tests for the `remove.pull_requests` field path."""

import pytest

from tests._jsonl import build_jsonl
from tests.state._helpers import build_state_from_jsonl


# ==================================================================================================
#  Happy path
# ==================================================================================================
def test_remove_closes_open_pr() -> None:
    # --- arrange / act ----------------
    jsonl = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "branch", "name": "feat", "from_branch": "main"},
        {"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"},
        {"op": "remove", "pull_requests": ["pr1"]},
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.pull_requests == {}


def test_remove_multiple_prs_in_one_op() -> None:
    # --- arrange / act ----------------
    jsonl = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "branch", "name": "feat1", "from_branch": "main"},
        {"op": "branch", "name": "feat2", "from_branch": "main"},
        {"op": "pull_request", "id": "pr1", "from": "feat1", "into": "main"},
        {"op": "pull_request", "id": "pr2", "from": "feat2", "into": "main"},
        {"op": "remove", "pull_requests": ["pr1", "pr2"]},
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.pull_requests == {}


# ==================================================================================================
#  Sad path — unknown id
# ==================================================================================================
def test_remove_unknown_pr_id_emits_e215() -> None:
    # --- arrange / act ----------------
    jsonl = build_jsonl({"op": "branch", "name": "main"}, {"op": "remove", "pull_requests": ["ghost"]})
    _state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    codes = {e.code for e in report.errors}
    assert "E215" in codes


def test_remove_continues_through_list_after_unknown_id() -> None:
    """One unknown id in the list doesn't stop the rest from being removed."""
    # --- arrange / act ----------------
    jsonl = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "branch", "name": "feat", "from_branch": "main"},
        {"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"},
        {"op": "remove", "pull_requests": ["ghost", "pr1"]},
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    codes = {e.code for e in report.errors}
    assert "E215" in codes
    # `pr1` was still removed despite the earlier unknown id.
    assert "pr1" not in state.pull_requests


# ==================================================================================================
#  Schema-level: exactly one of commits/branches/pull_requests must be set
# ==================================================================================================
@pytest.mark.parametrize(
    "raw",
    [
        build_jsonl({"op": "remove"}),
        build_jsonl({"op": "remove", "commits": ["c1"], "pull_requests": ["pr1"]}),
        build_jsonl({"op": "remove", "branches": ["b1"], "pull_requests": ["pr1"]}),
        build_jsonl({"op": "remove", "commits": ["c1"], "branches": ["b1"], "pull_requests": ["pr1"]}),
    ],
)
def test_remove_rejects_zero_or_multiple_kinds(raw: str) -> None:
    """The schema-level mutual-exclusion check rejects any combination other than exactly one."""
    # --- arrange / act ----------------
    _state, report = build_state_from_jsonl(raw + "\n")

    # --- assert -----------------------
    assert not report.is_clean()
