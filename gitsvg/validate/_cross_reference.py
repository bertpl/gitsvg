"""Cross-reference check — runs after every op has been applied.

The state engine is permissive about cross-references during apply: removing
a branch or commit that other entities reference is allowed, on the
expectation that the file will rebuild what it removed before the end.
This module is the "did it actually rebuild?" check that runs once over
the final state.

Two classes of dangling reference are flagged:

- A branch's `rooted_on_commit` (resolved at declaration time) no longer
  exists in current state — emitted as E400, attributed to the source
  line that declared the branch.
- A commit's `parents` references a commit that no longer exists —
  emitted as E401, attributed to the source line that introduced the
  commit. Each missing parent yields its own error.
"""

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.state import State


def check_cross_reference(state: State, report: ValidationReport) -> None:
    """Walk final state and emit errors for any dangling references.

    Args:
        state: The state produced by `apply_ops`.
        report: Report to which dangling-reference errors are appended.
    """
    _check_branch_roots(state, report)
    _check_commit_parents(state, report)


# ==================================================================================================
#  Per-class checks
# ==================================================================================================
def _check_branch_roots(state: State, report: ValidationReport) -> None:
    """Emit E400 for each branch whose captured root commit is no longer in state."""
    for branch in state.branches.values():
        if branch.rooted_on_commit is None:
            continue
        if state.has_commit(branch.rooted_on_commit):
            continue
        # rooted_on_commit was resolved from either from_branch's tip or from_commit.
        field = "from_commit" if branch.from_commit is not None else "from_branch"
        report.add(
            ValidationError(
                file=branch.declaration_file,
                line=branch.declaration_line,
                code="E400",
                message=(
                    f"branch {branch.name!r} is rooted on commit "
                    f"{branch.rooted_on_commit!r}, which has since been removed"
                ),
                field=field,
            )
        )


def _check_commit_parents(state: State, report: ValidationReport) -> None:
    """Emit E401 for each canonical parent that points at a removed commit.

    A commit's parents are resolved structurally (chain parent, plus the
    merged-in tip for a merge), so a dangling reference here means a
    `remove` op deleted a commit that some surviving commit still descends
    from — either its chain predecessor or a merged-in tip.
    """
    for commit in state.commits.values():
        for parent_id in commit.parents:
            if state.has_commit(parent_id):
                continue
            report.add(
                ValidationError(
                    file=commit.declaration_file,
                    line=commit.declaration_line,
                    code="E401",
                    message=(f"commit {commit.id!r} has a parent {parent_id!r} that has since been removed"),
                    field="parents",
                )
            )
