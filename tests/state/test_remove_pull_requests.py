"""Tests for the `remove.pull_requests` field path."""

import pytest

from tests.state._helpers import build_state_from_jsonl


# ==================================================================================================
#  Happy path
# ==================================================================================================
def test_remove_closes_open_pr() -> None:
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"}\n'
        '{"op": "remove", "pull_requests": ["pr1"]}\n'
    )
    state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    assert report.is_clean()
    assert state.pull_requests == {}


def test_remove_multiple_prs_in_one_op() -> None:
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat1", "from_branch": "main"}\n'
        '{"op": "branch", "name": "feat2", "from_branch": "main"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat1", "into": "main"}\n'
        '{"op": "pull_request", "id": "pr2", "from": "feat2", "into": "main"}\n'
        '{"op": "remove", "pull_requests": ["pr1", "pr2"]}\n'
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
    jsonl = '{"op": "branch", "name": "main"}\n{"op": "remove", "pull_requests": ["ghost"]}\n'
    _state, report = build_state_from_jsonl(jsonl)

    # --- assert -----------------------
    codes = {e.code for e in report.errors}
    assert "E215" in codes


def test_remove_continues_through_list_after_unknown_id() -> None:
    """One unknown id in the list doesn't stop the rest from being removed."""
    # --- arrange / act ----------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main"}\n'
        '{"op": "remove", "pull_requests": ["ghost", "pr1"]}\n'
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
        '{"op": "remove"}',
        '{"op": "remove", "commits": ["c1"], "pull_requests": ["pr1"]}',
        '{"op": "remove", "branches": ["b1"], "pull_requests": ["pr1"]}',
        '{"op": "remove", "commits": ["c1"], "branches": ["b1"], "pull_requests": ["pr1"]}',
    ],
)
def test_remove_rejects_zero_or_multiple_kinds(raw: str) -> None:
    """The schema-level mutual-exclusion check rejects any combination other than exactly one."""
    # --- arrange / act ----------------
    _state, report = build_state_from_jsonl(raw + "\n")

    # --- assert -----------------------
    assert not report.is_clean()
