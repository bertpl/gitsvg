"""State engine — apply parsed ops in order, accumulating semantic errors.

`apply_ops` is the only entry point. It dispatches each `ParsedOp` to
the right per-op handler under `gitsvg.state._apply`, accumulating
semantic errors into the provided `ValidationReport`. Shape-failed
lines never reach this layer — they were dropped by the parser before
becoming `ParsedOp` records.

`import` ops are skipped here. Import resolution lands in a later
version; in this layer they're shape-only.
"""

from gitsvg.errors import ValidationReport
from gitsvg.file_format.ops import (
    BranchOp,
    CanvasOp,
    CommitOp,
    HighlightOp,
    ImportOp,
    MergeOp,
    RemoveOp,
)
from gitsvg.parse import ParsedOp
from gitsvg.state._apply import (
    apply_branch_op,
    apply_canvas_op,
    apply_commit_op,
    apply_highlight_op,
    apply_merge_op,
    apply_remove_op,
)
from gitsvg.state._state import State


def apply_ops(parsed_ops: list[ParsedOp], report: ValidationReport) -> State:
    """Apply parsed ops to a fresh state, accumulating semantic errors into `report`.

    Args:
        parsed_ops: Shape-validated ops in source order.
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
    elif isinstance(op, RemoveOp):
        apply_remove_op(state, parsed, report)
    elif isinstance(op, HighlightOp):
        apply_highlight_op(state, parsed, report)
    elif isinstance(op, CanvasOp):
        apply_canvas_op(state, parsed, report)
    elif isinstance(op, ImportOp):
        # Import resolution lands in a later version; this layer is shape-only.
        return
