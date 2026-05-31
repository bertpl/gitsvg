"""State engine — apply parsed ops in order, producing `(State, Theme)`.

`apply_ops` is the only entry point. It dispatches each `ParsedOp` to
the right per-op handler — state-mutating handlers under
`gitsvg.state._apply`, the theme-mutating handler under
`gitsvg.theme._apply` — accumulating semantic errors into the
provided `ValidationReport`. Schema-failed lines never reach this
layer; they were dropped by the parser before becoming `ParsedOp`
records.

Theme construction threads a single `ThemeBuilder` through the apply
pass. Theme ops mutate the builder's `theme_cls` and `user_set` (and,
when a name-bearing op leaves `keep_prior_overrides` at its default
`False`, wipe both `user_set` and `branch_color_overrides`); branch /
remove ops mutate the builder's `branch_color_overrides`; every other
op handler receives the builder for signature uniformity but leaves
it alone. The engine calls `builder.build()` once at end-of-apply to
produce the fully-resolved `Theme`.

`import` ops are expanded away upstream by `gitsvg.imports.resolve_imports`
before `apply_ops` runs, so they normally do not reach the engine. Any
leftover `ImportOp` (e.g. when a caller skips the resolver) is treated
as a no-op here.
"""

from gitsvg.errors import ValidationError, ValidationReport
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
from gitsvg.theme import Theme, ThemeBuilder

# Leaf-path import: pulls in `State` for the shared handler signature,
# so the package-level `gitsvg.theme.__init__` deliberately does not
# re-export `apply_theme_op` (cycle-avoidance pattern matching
# `file_format/ops/framework/`).
from gitsvg.theme._apply import apply_theme_op


def apply_ops(parsed_ops: list[ParsedOp], report: ValidationReport) -> tuple[State, Theme]:
    """Apply parsed ops to a fresh `(State, Theme)`, accumulating semantic errors.

    Threads a single `ThemeBuilder` through the apply pass — theme,
    branch, and remove handlers mutate it; other handlers ignore it.
    At end-of-apply the builder produces the fully-resolved `Theme`
    via its chosen subclass's `build(user_set)` classmethod, with
    state-derived per-branch colour overrides written onto the result.

    Args:
        parsed_ops: Schema-validated ops in source order.
        report: Report to which semantic errors are appended. The report
            may already hold parser errors; this function only adds.

    Returns:
        `(state, theme)` — the fully-applied structural state and the
        fully-resolved theme. Even when errors occur, every op is
        attempted and the surviving pair is returned for inspection.
    """
    state = State()
    builder = ThemeBuilder()
    for parsed in parsed_ops:
        _apply_one(state, builder, parsed, report)
    theme = builder.build()
    _check_auto_lane_change_conflicts(state, builder, theme, report)
    return state, theme


def _check_auto_lane_change_conflicts(
    state: State, builder: ThemeBuilder, theme: Theme, report: ValidationReport
) -> None:
    """Emit the `auto_lane_change` mutual-exclusion errors (E221, E222).

    Both checks need the resolved `Theme` (the flag value) plus a side
    input the resolved theme alone can't supply — the per-branch pins on
    `State` for E221, and which fields the user explicitly set
    (`ThemeBuilder.user_set`) for E222. So they live here at the
    `apply_ops` orchestration point rather than in the state-only
    end-of-file pass or the per-op theme-apply handler.

    Args:
        state: The fully-applied state, carrying per-branch pins.
        builder: The theme builder, carrying the explicit `user_set`
            overrides and their originating op lines.
        theme: The resolved theme, carrying `auto_lane_change` and
            `merge_lane_clearance`.
        report: Receives the conflict errors.
    """
    _check_branch_pos_conflicts(state, theme, report)
    _check_merge_lane_clearance_conflict(builder, theme, report)


def _check_branch_pos_conflicts(state: State, theme: Theme, report: ValidationReport) -> None:
    """Emit E221 for each `branch_pos:` pin when `auto_lane_change` is on.

    A pin fixes a branch's lane for life; `auto_lane_change` keeps lanes
    free to migrate. The two are mutually exclusive.

    Args:
        state: The fully-applied state, carrying per-branch pins.
        theme: The resolved theme, carrying `auto_lane_change`.
        report: Receives one E221 per pinned branch.
    """
    if not theme.auto_lane_change:
        return
    for branch in state.branches.values():
        if branch.branch_pos is None:
            continue
        report.add(
            ValidationError(
                file=branch.declaration_file,
                line=branch.declaration_line,
                code="E221",
                message=(
                    f"branch {branch.name!r} sets branch_pos, which conflicts with "
                    f"theme.auto_lane_change (a pinned lane cannot also migrate)"
                ),
                field="branch_pos",
            )
        )


def _check_merge_lane_clearance_conflict(builder: ThemeBuilder, theme: Theme, report: ValidationReport) -> None:
    """Emit E222 when `merge_lane_clearance` is set while `auto_lane_change` is off.

    `merge_lane_clearance` only governs how a migrating sibling repacks
    around a merged source's reserved lane — machinery the flag-off path
    never runs. An explicit value under a disabled flag is therefore dead
    config and is rejected rather than silently ignored.

    The trigger is membership in `builder.user_set`, not value-≠-default:
    the user set the field, which is the mistake, even at its default `1`.
    Checking at end-of-apply (not per-op) means a named-theme switch that
    wipes prior overrides — the default `keep_prior_overrides=False`
    behaviour — clears the field from `user_set` first, so switching
    themes is the documented escape hatch.

    Args:
        builder: The theme builder, carrying `user_set` and the
            originating op lines (`user_set_lines`).
        theme: The resolved theme, carrying `auto_lane_change`.
        report: Receives one E222 when the conflict holds.
    """
    if theme.auto_lane_change:
        return
    if "merge_lane_clearance" not in builder.user_set:
        return
    file, line = builder.user_set_lines["merge_lane_clearance"]
    report.add(
        ValidationError(
            file=file,
            line=line,
            code="E222",
            message=(
                "theme.merge_lane_clearance has no effect unless theme.auto_lane_change "
                "is enabled (enable auto_lane_change or drop merge_lane_clearance)"
            ),
            field="merge_lane_clearance",
        )
    )


def _apply_one(state: State, builder: ThemeBuilder, parsed: ParsedOp, report: ValidationReport) -> None:
    """Dispatch a single parsed op to its handler."""
    op = parsed.op
    if isinstance(op, BranchOp):
        apply_branch_op(state, builder, parsed, report)
    elif isinstance(op, CommitOp):
        apply_commit_op(state, builder, parsed, report)
    elif isinstance(op, MergeOp):
        apply_merge_op(state, builder, parsed, report)
    elif isinstance(op, PullRequestOp):
        apply_pull_request_op(state, builder, parsed, report)
    elif isinstance(op, RemoveOp):
        apply_remove_op(state, builder, parsed, report)
    elif isinstance(op, HighlightOp):
        apply_highlight_op(state, builder, parsed, report)
    elif isinstance(op, GridOp):
        apply_grid_op(state, builder, parsed, report)
    elif isinstance(op, ThemeOp):
        apply_theme_op(state, builder, parsed, report)
    elif isinstance(op, ImportOp):
        # Import ops are normally expanded away by gitsvg.imports.resolve_imports
        # before apply_ops runs; treat any leftover as a no-op.
        return
