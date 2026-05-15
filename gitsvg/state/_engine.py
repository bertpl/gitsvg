"""State engine — apply parsed ops in order, producing `(State, Theme)`.

`apply_ops` is the only entry point. It dispatches each `ParsedOp` to
the right per-op handler — state-mutating handlers under
`gitsvg.state._apply`, the theme-mutating handler under
`gitsvg.theme._apply` — accumulating semantic errors into the
provided `ValidationReport`. Schema-failed lines never reach this
layer; they were dropped by the parser before becoming `ParsedOp`
records.

`import` ops are expanded away upstream by `gitsvg.imports.resolve_imports`
before `apply_ops` runs, so they normally do not reach the engine. Any
leftover `ImportOp` (e.g. when a caller skips the resolver) is treated
as a no-op here.
"""

import copy

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
)
from gitsvg.state._state import State
from gitsvg.theme import DEFAULT_THEME, Theme, resolve_defaults

# Leaf-path import: pulls in `State` for the shared handler signature,
# so the package-level `gitsvg.theme.__init__` deliberately does not
# re-export `apply_theme_op` (cycle-avoidance pattern matching
# `file_format/ops/framework/`).
from gitsvg.theme._apply import apply_theme_op


def apply_ops(parsed_ops: list[ParsedOp], report: ValidationReport) -> tuple[State, Theme]:
    """Apply parsed ops to a fresh `(State, Theme)`, accumulating semantic errors.

    Args:
        parsed_ops: Schema-validated ops in source order.
        report: Report to which semantic errors are appended. The report
            may already hold parser errors; this function only adds.

    Returns:
        `(state, theme)` — the fully-applied structural state and the
        fully-resolved theme. Even when errors occur, every op is
        attempted and the surviving pair is returned for inspection.
        `resolve_defaults` runs as the final step so the renderer sees
        no `None`-default sentinel on any orientation-resolved field.
    """
    state = State()
    theme = copy.deepcopy(DEFAULT_THEME)
    for parsed in parsed_ops:
        _apply_one(state, theme, parsed, report)
    resolve_defaults(theme)
    return state, theme


def _apply_one(state: State, theme: Theme, parsed: ParsedOp, report: ValidationReport) -> None:
    """Dispatch a single parsed op to its handler."""
    op = parsed.op
    if isinstance(op, BranchOp):
        apply_branch_op(state, theme, parsed, report)
    elif isinstance(op, CommitOp):
        apply_commit_op(state, theme, parsed, report)
    elif isinstance(op, MergeOp):
        apply_merge_op(state, theme, parsed, report)
    elif isinstance(op, PullRequestOp):
        apply_pull_request_op(state, theme, parsed, report)
    elif isinstance(op, RemoveOp):
        apply_remove_op(state, theme, parsed, report)
    elif isinstance(op, HighlightOp):
        apply_highlight_op(state, theme, parsed, report)
    elif isinstance(op, GridOp):
        apply_grid_op(state, theme, parsed, report)
    elif isinstance(op, ThemeOp):
        apply_theme_op(state, theme, parsed, report)
    elif isinstance(op, ImportOp):
        # Import ops are normally expanded away by gitsvg.imports.resolve_imports
        # before apply_ops runs; treat any leftover as a no-op.
        return
