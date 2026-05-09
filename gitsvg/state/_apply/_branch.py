"""Apply a `branch` op to state — root resolution + uniqueness check."""

from typing import cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import BranchOp
from gitsvg.parse import ParsedOp
from gitsvg.state._state import BranchState, State


def apply_branch_op(state: State, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `branch` op.

    Validation order:

    1. Branch name must not already be declared (E202).
    2. Non-first branch must specify exactly one of `from_branch` / `from_commit` (E204).
       (The "at most one" half is structural — enforced by the pydantic model on
       `BranchOp`. The "at least one" half needs runtime state, so it lives here.)
    3. `from_branch` (when set) must reference an existing branch (E200).
       Diagnostic note: when the name exists as a commit id instead, the
       message hints at using `from_commit`.
    4. `from_commit` (when set) must reference an existing commit (E201).
       Same kind-typed hint applies.

    On any failure the branch is not added to state.
    """
    op = cast(BranchOp, parsed.op)
    file = parsed.file
    line = parsed.line

    # --- Uniqueness -----------------------------
    if op.name in state.branches:
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E202",
                message=f"branch {op.name!r} is already declared",
                field="name",
            )
        )
        return

    # --- Root presence --------------------------
    is_first = state.is_first_branch()
    has_root = op.from_branch is not None or op.from_commit is not None
    if not is_first and not has_root:
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E204",
                message=(f"non-first branch {op.name!r} must specify one of 'from_branch' or 'from_commit'"),
            )
        )
        return

    # --- from_branch existence ------------------
    rooted_on: str | None = None
    if op.from_branch is not None:
        if not state.has_branch(op.from_branch):
            hint = (
                f" (a commit with id {op.from_branch!r} exists — did you mean 'from_commit'?)"
                if state.has_commit(op.from_branch)
                else ""
            )
            report.add(
                ValidationError(
                    file=file,
                    line=line,
                    code="E200",
                    message=f"branch {op.from_branch!r} is not declared{hint}",
                    field="from_branch",
                )
            )
            return
        rooted_on = state.branch_tip(op.from_branch)

    # --- from_commit existence ------------------
    if op.from_commit is not None:
        if not state.has_commit(op.from_commit):
            hint = (
                f" (a branch named {op.from_commit!r} exists — did you mean 'from_branch'?)"
                if state.has_branch(op.from_commit)
                else ""
            )
            report.add(
                ValidationError(
                    file=file,
                    line=line,
                    code="E201",
                    message=f"commit {op.from_commit!r} is not declared{hint}",
                    field="from_commit",
                )
            )
            return
        rooted_on = op.from_commit

    # --- Add to state ---------------------------
    state.branches[op.name] = BranchState(
        name=op.name,
        color=op.color,
        label_side=op.label_side,
        branch_pos=op.branch_pos,
        from_branch=op.from_branch,
        from_commit=op.from_commit,
        rooted_on_commit=rooted_on,
        declaration_file=file,
        declaration_line=line,
    )
    state.branch_order.append(op.name)
