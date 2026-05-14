"""Apply a `remove` op to state — destructive removal of commits, branches, or pull-requests."""

from typing import cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import RemoveOp
from gitsvg.parse import ParsedOp
from gitsvg.state._state import State
from gitsvg.theme import Theme


def apply_remove_op(state: State, theme: Theme, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `remove` op.

    Removes either commits, branches, or pull-requests (the schema
    phase guarantees exactly one of the three list fields is set).
    Removing a branch cascades to its commits.

    Targets that don't exist in current state produce E200/E201/E214
    errors but the rest of the list still attempts to remove. This
    matches the format spec's permissive stance on cross-references —
    dangling references are tolerated mid-file and end-of-file
    validation (`check_end_of_file` in `gitsvg.state._eof`) flags any
    that aren't restored.

    Branch removal also enforces that no open pull-request still
    references the branch as either `from` or `into` (E214) — explicit
    close-before-remove keeps the PR lifecycle legible.
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
            blocking_prs = [
                pr for pr in state.pull_requests.values() if branch_name in (pr.from_branch, pr.into_branch)
            ]
            if blocking_prs:
                pr_ids = ", ".join(repr(pr.id) for pr in blocking_prs)
                report.add(
                    ValidationError(
                        file=file,
                        line=line,
                        code="E214",
                        message=(
                            f"cannot remove branch {branch_name!r}: open pull_request(s) {pr_ids} "
                            f"still reference it; close them first"
                        ),
                        field=f"branches.{index}",
                    )
                )
                continue
            _remove_branch_with_cascade(state, theme, branch_name)
        return

    if op.pull_requests:
        for index, pr_id in enumerate(op.pull_requests):
            if not state.has_pull_request(pr_id):
                report.add(
                    ValidationError(
                        file=file,
                        line=line,
                        code="E215",
                        message=f"pull_request {pr_id!r} is not declared",
                        field=f"pull_requests.{index}",
                    )
                )
                continue
            state.pull_requests.pop(pr_id, None)


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


def _remove_branch_with_cascade(state: State, theme: Theme, branch_name: str) -> None:
    """Drop a branch (and every commit on it) from state, plus its theme override.

    Removing a branch cleans up `theme.branch_color_overrides[branch.id]`
    so a redeclared branch with the same name doesn't inherit the
    removed branch's colour through a stale entry, and the dict stays
    aligned with the set of live branch ids.
    """
    branch = state.branches.pop(branch_name, None)
    if branch is None:
        return
    if branch_name in state.branch_order:
        state.branch_order.remove(branch_name)
    for commit_id in list(branch.commit_ids):
        state.commits.pop(commit_id, None)
    theme.branch_color_overrides.pop(branch.id, None)
