"""Apply a `remove` op to state — destructive removal of commits or branches."""

from typing import cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import RemoveOp
from gitsvg.parse import ParsedOp
from gitsvg.state._state import State


def apply_remove_op(state: State, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `remove` op.

    Removes either commits or branches (the shape phase guarantees
    exactly one of the two list fields is set). Removing a branch
    cascades to its commits.

    Targets that don't exist in current state produce E200/E201 errors
    but the rest of the list still attempts to remove. This matches
    the format spec's permissive stance on cross-references — dangling
    references are tolerated mid-file and end-of-file validation
    (a later layer) flags any that aren't restored.
    """
    op = cast(RemoveOp, parsed.op)
    file = parsed.file
    line = parsed.line

    if op.commits:
        for index, commit_id in enumerate(op.commits):
            if not state.has_commit(commit_id):
                report.add(
                    ValidationError(
                        file=file,
                        line=line,
                        code="E201",
                        message=f"commit {commit_id!r} is not declared",
                        field=f"commits.{index}",
                    )
                )
                continue
            _remove_commit(state, commit_id)
        return

    if op.branches:
        for index, branch_name in enumerate(op.branches):
            if not state.has_branch(branch_name):
                report.add(
                    ValidationError(
                        file=file,
                        line=line,
                        code="E200",
                        message=f"branch {branch_name!r} is not declared",
                        field=f"branches.{index}",
                    )
                )
                continue
            _remove_branch_with_cascade(state, branch_name)


# ==================================================================================================
#  Helpers
# ==================================================================================================
def _remove_commit(state: State, commit_id: str) -> None:
    """Drop a commit from state and from its branch's commit-ids list."""
    commit = state.commits.pop(commit_id, None)
    if commit is None:
        return
    branch = state.branches.get(commit.branch)
    if branch is not None and commit_id in branch.commit_ids:
        branch.commit_ids.remove(commit_id)


def _remove_branch_with_cascade(state: State, branch_name: str) -> None:
    """Drop a branch and every commit on it from state."""
    branch = state.branches.pop(branch_name, None)
    if branch is None:
        return
    if branch_name in state.branch_order:
        state.branch_order.remove(branch_name)
    for commit_id in list(branch.commit_ids):
        state.commits.pop(commit_id, None)
