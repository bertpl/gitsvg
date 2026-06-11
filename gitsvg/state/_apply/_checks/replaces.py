"""The `replaces:` semantic-rule check, factored out of the commit-op handler.

`check_replaces_rules` is invoked by `_apply/_commit.py` before any state
mutation. It validates the replaces field against current state and returns
True only when all applicable rules pass. Errors are appended to the report
as they're discovered.

Rule numbering follows the locked-in format spec; rule 6 (tags/annotate)
is reserved and currently dormant, and rule 7 (the squash commit's own
parents disjoint from the replaced set) retired with the removal of
author-declared commit parents — a commit can no longer name a parent, so
the rule became vacuous.
"""

from typing import TYPE_CHECKING, cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.parse import ParsedOp
from gitsvg.state._apply._errors import add_commit_not_declared
from gitsvg.state._state import State

if TYPE_CHECKING:
    from gitsvg.file_format.ops import CommitOp


def check_replaces_rules(state: State, parsed: ParsedOp, report: ValidationReport) -> bool:
    """Validate the `replaces:` rules for the given commit op.

    Args:
        state: Current state (pre-mutation).
        parsed: The parsed commit op being applied.
        report: Report receiving any rule violations.

    Returns:
        True when every rule passes (and the caller may proceed to apply
        the squash). False when any rule fails — the caller should skip
        applying the op.
    """
    op = cast("CommitOp", parsed.op)
    file = parsed.file
    line = parsed.line
    replaces = list(op.replaces or [])
    replaced_set = set(replaces)
    target_branch = op.branch

    if not _check_rule_1_existence(state, replaces, file, line, report):
        return False
    if not _check_rule_2_same_branch(state, replaces, target_branch, file, line, report):
        return False
    if not _check_rule_3_contiguous_tail(state, replaces, replaced_set, target_branch, file, line, report):
        return False
    if not _check_rule_4_no_other_branch_rooted(state, replaced_set, target_branch, file, line, report):
        return False
    return _check_rule_5_no_external_parents(state, replaced_set, file, line, report)


# ==================================================================================================
#  Rule 1 — every replaced id must exist in current state
# ==================================================================================================
def _check_rule_1_existence(
    state: State,
    replaces: list[str],
    file: str,
    line: int,
    report: ValidationReport,
) -> bool:
    """Rule 1: every id in `replaces:` exists in current state."""
    for rid in replaces:
        if not state.has_commit(rid):
            add_commit_not_declared(
                report, file=file, line=line, commit_id=rid, field="replaces", declared=state.commits
            )
            return False
    return True


# ==================================================================================================
#  Rule 2 — every replaced commit on the same branch as the new commit
# ==================================================================================================
def _check_rule_2_same_branch(
    state: State,
    replaces: list[str],
    target_branch: str,
    file: str,
    line: int,
    report: ValidationReport,
) -> bool:
    """Rule 2: replaced commits must all live on the new commit's branch."""
    for rid in replaces:
        actual = state.commits[rid].branch
        if actual != target_branch:
            report.add(
                ValidationError(
                    file=file,
                    line=line,
                    code="E205",
                    message=(
                        f"replaces commit {rid!r} is on branch {actual!r}, "
                        f"not {target_branch!r} (the new commit's branch)"
                    ),
                    field="replaces",
                )
            )
            return False
    return True


# ==================================================================================================
#  Rule 3 — replaced commits form a contiguous tail of the branch
# ==================================================================================================
def _check_rule_3_contiguous_tail(
    state: State,
    replaces: list[str],
    replaced_set: set[str],
    target_branch: str,
    file: str,
    line: int,
    report: ValidationReport,
) -> bool:
    """Rule 3: replaced commits must form a contiguous range at the tail of the branch."""
    branch_commits = state.branches[target_branch].commit_ids
    n = len(replaces)
    tail = branch_commits[-n:] if n <= len(branch_commits) else branch_commits
    if len(tail) != n or set(tail) != replaced_set:
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E206",
                message=(
                    f"replaces ids do not form a contiguous tail of branch {target_branch!r} "
                    f"(branch tip-to-back: {list(reversed(branch_commits))})"
                ),
                field="replaces",
            )
        )
        return False
    return True


# ==================================================================================================
#  Rule 4 — no other branch rooted on a replaced commit
# ==================================================================================================
def _check_rule_4_no_other_branch_rooted(
    state: State,
    replaced_set: set[str],
    target_branch: str,
    file: str,
    line: int,
    report: ValidationReport,
) -> bool:
    """Rule 4: no branch other than the target branch is rooted on a replaced commit."""
    for branch_name, branch in state.branches.items():
        if branch_name == target_branch:
            continue
        if branch.rooted_on_commit in replaced_set:
            report.add(
                ValidationError(
                    file=file,
                    line=line,
                    code="E207",
                    message=(
                        f"branch {branch_name!r} is rooted on commit {branch.rooted_on_commit!r} which is in `replaces`"
                    ),
                    field="replaces",
                )
            )
            return False
    return True


# ==================================================================================================
#  Rule 5 — no external commit's parents reference a replaced commit
# ==================================================================================================
def _check_rule_5_no_external_parents(
    state: State,
    replaced_set: set[str],
    file: str,
    line: int,
    report: ValidationReport,
) -> bool:
    """Rule 5: no commit outside the replaced set has parents referencing a replaced commit."""
    for cid, commit in state.commits.items():
        if cid in replaced_set:
            continue
        for parent_id in commit.parents:
            if parent_id in replaced_set:
                report.add(
                    ValidationError(
                        file=file,
                        line=line,
                        code="E208",
                        message=(f"commit {cid!r} has parents referencing {parent_id!r} which is in `replaces`"),
                        field="replaces",
                    )
                )
                return False
    return True
