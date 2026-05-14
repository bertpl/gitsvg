"""Apply a `branch` op — root resolution, uniqueness check, optional theme colour."""

from typing import cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import BranchOp
from gitsvg.parse import ParsedOp
from gitsvg.state._state import BranchState, State
from gitsvg.theme import Theme


def apply_branch_op(state: State, theme: Theme, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `branch` op.

    Mutates `state` for the structural side (new `BranchState`,
    branch-order append) and `theme` for the presentational side
    (writes `op.color`, when set, to `theme.branch_color_overrides`
    keyed by the new branch's id).

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

    On any failure neither state nor theme is mutated.
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
    branch_id = state.next_branch_id()
    state.branches[op.name] = BranchState(
        id=branch_id,
        name=op.name,
        label_side=op.label_side,
        branch_pos=op.branch_pos,
        from_branch=op.from_branch,
        from_commit=op.from_commit,
        rooted_on_commit=rooted_on,
        declaration_file=file,
        declaration_line=line,
    )
    state.branch_order.append(op.name)

    # --- Theme: per-branch colour override ------
    if op.color is not None:
        theme.branch_color_overrides[branch_id] = op.color
