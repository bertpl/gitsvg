"""State engine — apply parsed ops in order, accumulating semantic errors.

`apply_ops` is the only entry point. It dispatches each `ParsedOp` to
the right per-op handler under `gitsvg.state._apply`, accumulating
semantic errors into the provided `ValidationReport`. Schema-failed
lines never reach this layer — they were dropped by the parser before
becoming `ParsedOp` records.

`import` ops are expanded away upstream by `gitsvg.imports.resolve_imports`
before `apply_ops` runs, so they normally do not reach the engine. Any
leftover `ImportOp` (e.g. when a caller skips the resolver) is treated
as a no-op here.
"""

from gitsvg.errors import ValidationReport
from gitsvg.file_format.ops import (
    BranchOp,
    CommitOp,
    GridOp,
    HighlightOp,
    ImportOp,
    MergeOp,
    PullRequestOp,
    RemoveOp,
    ThemeOp,
)
from gitsvg.parse import ParsedOp
from gitsvg.state._apply import (
    apply_branch_op,
    apply_commit_op,
    apply_grid_op,
    apply_highlight_op,
    apply_merge_op,
    apply_pull_request_op,
    apply_remove_op,
    apply_theme_op,
)
from gitsvg.state._state import State


def apply_ops(parsed_ops: list[ParsedOp], report: ValidationReport) -> State:
    """Apply parsed ops to a fresh state, accumulating semantic errors into `report`.

    Args:
        parsed_ops: Schema-validated ops in source order.
        report: Report to which semantic errors are appended. The report
            may already hold parser errors; this function only adds.

    Returns:
        The fully-applied `State`. Even when errors occur, every op is
        attempted and the surviving state is returned for inspection.
    """
    state = State()
    for parsed in parsed_ops:
        _apply_one(state, parsed, report)
    return state


def _apply_one(state: State, parsed: ParsedOp, report: ValidationReport) -> None:
    """Dispatch a single parsed op to its handler."""
    op = parsed.op
    if isinstance(op, BranchOp):
        apply_branch_op(state, parsed, report)
    elif isinstance(op, CommitOp):
        apply_commit_op(state, parsed, report)
    elif isinstance(op, MergeOp):
        apply_merge_op(state, parsed, report)
    elif isinstance(op, PullRequestOp):
        apply_pull_request_op(state, parsed, report)
    elif isinstance(op, RemoveOp):
        apply_remove_op(state, parsed, report)
    elif isinstance(op, HighlightOp):
        apply_highlight_op(state, parsed, report)
    elif isinstance(op, GridOp):
        apply_grid_op(state, parsed, report)
    elif isinstance(op, ThemeOp):
        apply_theme_op(state, parsed, report)
    elif isinstance(op, ImportOp):
        # Import ops are normally expanded away by gitsvg.imports.resolve_imports
        # before apply_ops runs; treat any leftover as a no-op.
        return
