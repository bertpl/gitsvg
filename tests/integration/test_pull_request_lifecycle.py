"""End-to-end validate test for the `pull_request` happy-path lifecycle.

Exercises the locked sequence: declare PR → commits on both sides →
remove PR → merge. Asserts that every intermediate step validates
cleanly and that the final state holds the expected entities.
"""

from gitsvg.errors import ValidationReport
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops, check_end_of_file


def _validate(jsonl: str) -> tuple[ValidationReport, object]:
    """Run parse + apply + EOF check on `jsonl` and return `(report, state)`."""
    parsed, report = parse_jsonl_text(jsonl, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    check_end_of_file(state, report)
    return report, state


def test_pull_request_full_lifecycle_validates_clean() -> None:
    # --- arrange ----------------------
    jsonl = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "initial"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "wip"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main", "title": "Add the thing"}\n'
        '{"op": "commit", "branch": "feat", "id": "f2", "msg": "polish"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "side fix"}\n'
        '{"op": "remove", "pull_requests": ["pr1"]}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "merged", "msg": "merge feat"}\n'
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
