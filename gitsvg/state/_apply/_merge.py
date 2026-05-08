"""Apply a `merge` op to state — emits a two-parent commit on `into`."""

from typing import cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import MergeOp
from gitsvg.parse import ParsedOp
from gitsvg.state._apply._commit import _generate_auto_commit_id
from gitsvg.state._state import CommitState, State


def apply_merge_op(state: State, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `merge` op.

    A merge produces a commit on `into` whose parents are the prior tip
    of `into` and the current tip of `from`. When the optional `as`
    field is set, the new commit takes that id; otherwise it is
    auto-generated.

    Validation:

    1. `from` must reference an existing branch (E200).
    2. `into` must reference an existing branch (E200).
    3. When `as:` is set, the id must not already be used (E203).
    """
    op = cast(MergeOp, parsed.op)
    file = parsed.file
    line = parsed.line

    if not state.has_branch(op.from_):
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E200",
                message=f"branch {op.from_!r} is not declared",
                field="from",
            )
        )
        return

    if not state.has_branch(op.into):
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E200",
                message=f"branch {op.into!r} is not declared",
                field="into",
            )
        )
        return

    explicit_id = op.as_
    merge_id = explicit_id if explicit_id is not None else _generate_auto_commit_id(state)
    if explicit_id is not None and explicit_id in state.commits:
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E203",
                message=f"commit id {explicit_id!r} is already used",
                field="as",
            )
        )
        return

    parents = [tip for tip in (state.branch_tip(op.into), state.branch_tip(op.from_)) if tip is not None]

    state.commits[merge_id] = CommitState(
        id=merge_id,
        branch=op.into,
        msg=op.msg,
        parents=parents,
        declaration_line=line,
    )
    state.branches[op.into].commit_ids.append(merge_id)
