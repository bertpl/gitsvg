"""End-to-end validate test for the `pull_request` happy-path lifecycle.

Exercises the locked sequence: declare PR → commits on both sides →
remove PR → merge. Asserts that every intermediate step validates
cleanly and that the final state holds the expected entities.
"""

from gitsvg.cli._pipeline import apply_and_validate
from gitsvg.errors import ValidationReport
from gitsvg.parse import parse_jsonl_text
from tests._jsonl import build_jsonl


def _validate(jsonl: str) -> tuple[ValidationReport, object]:
    """Run parse + apply + validation on `jsonl` and return `(report, state)`."""
    parsed, report = parse_jsonl_text(jsonl, file="x.jsonl")
    state, _theme = apply_and_validate(parsed, report)
    return report, state


def test_pull_request_full_lifecycle_validates_clean() -> None:
    # --- arrange ----------------------
    jsonl = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "m1", "msg": "initial"},
        {"op": "branch", "name": "feat", "from_branch": "main"},
        {"op": "commit", "branch": "feat", "id": "f1", "msg": "wip"},
        {"op": "pull_request", "id": "pr1", "from": "feat", "into": "main", "title": "Add the thing"},
        {"op": "commit", "branch": "feat", "id": "f2", "msg": "polish"},
        {"op": "commit", "branch": "main", "id": "m2", "msg": "side fix"},
        {"op": "remove", "pull_requests": ["pr1"]},
        {"op": "merge", "from": "feat", "into": "main", "as": "merged", "msg": "merge feat"},
    )

    # --- act --------------------------
    report, state = _validate(jsonl)

    # --- assert -----------------------
    assert report.is_clean(), f"unexpected errors: {[e.format() for e in report.errors]}"
    assert state.pull_requests == {}
    assert state.has_commit("merged")
    assert "merged" in state.branches["main"].commit_ids
    # Both branches accumulated commits while the PR was open.
    assert state.branches["feat"].commit_ids == ["f1", "f2"]
    # main: m1, m2, merged (the merge commit).
    assert state.branches["main"].commit_ids == ["m1", "m2", "merged"]
