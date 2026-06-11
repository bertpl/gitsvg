"""Apply a `remove` op to state — destructive removal of commits, branches, or pull-requests."""

from typing import TYPE_CHECKING, cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.parse import ParsedOp
from gitsvg.state._apply._errors import add_branch_not_declared, add_commit_not_declared
from gitsvg.state._state import State
from gitsvg.theme import ThemeBuilder

if TYPE_CHECKING:
    from gitsvg.file_format.ops import RemoveOp


def apply_remove_op(state: State, builder: ThemeBuilder, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `remove` op.

    Removes either commits, branches, or pull-requests (the schema
    phase guarantees exactly one of the three list fields is set).
    Removing a branch cascades to its commits.

    Targets that don't exist in current state produce E200/E201/E214
    errors but the rest of the list still attempts to remove. This
    matches the format spec's permissive stance on cross-references —
    dangling references are tolerated mid-file and the cross-reference
    validation (`check_cross_reference` in `gitsvg.validate`) flags any
    that aren't restored.

    Branch removal also enforces that no open pull-request still
    references the branch as either `from` or `into` (E214) — explicit
    close-before-remove keeps the PR lifecycle legible.
    """
    op = cast("RemoveOp", parsed.op)
    file = parsed.file
    line = parsed.line

    if op.commits:
        for index, commit_id in enumerate(op.commits):
            if not state.has_commit(commit_id):
                add_commit_not_declared(
                    report, file=file, line=line, commit_id=commit_id, field=f"commits.{index}", declared=state.commits
                )
                continue
            state.remove_commit(commit_id)
        return

    if op.branches:
        for index, branch_name in enumerate(op.branches):
            if not state.has_branch(branch_name):
                add_branch_not_declared(
                    report, file=file, line=line, branch=branch_name, field=f"branches.{index}", declared=state.branches
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
            _remove_branch_with_cascade(state, builder, branch_name)
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
def _remove_branch_with_cascade(state: State, builder: ThemeBuilder, branch_name: str) -> None:
    """Drop a branch (and every commit on it) from state, plus its theme overrides.

    Removing a branch cleans up every per-branch entry on `builder`
    keyed by the branch's id (`branch_color_overrides`,
    `branch_label_side_overrides`) so a redeclared branch with the
    same name doesn't inherit the removed branch's presentational
    choices through stale entries, and each dict stays aligned with
    the set of live branch ids.
    """
    branch = state.branches.pop(branch_name, None)
    if branch is None:
        return
    if branch_name in state.branch_order:
        state.branch_order.remove(branch_name)
    for commit_id in list(branch.commit_ids):
        state.remove_commit(commit_id)
    builder.branch_color_overrides.pop(branch.id, None)
    builder.branch_label_side_overrides.pop(branch.id, None)
