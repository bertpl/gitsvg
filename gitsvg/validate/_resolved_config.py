"""Resolved-config consistency checks (E221-E224).

Cross-field theme-configuration conflicts that can only be decided once
the whole op stream is applied and the theme is fully resolved — a later
named-theme switch can wipe an earlier setting, so only the final
resolved theme is meaningful. Each check reads the resolved `Theme` plus
the `UserOverrides` record of what was explicitly set; none needs the
full `State`.

- E221: a `branch_pos` pin conflicts with `theme.auto_lane_change`.
- E222: `theme.merge_lane_clearance` set while `auto_lane_change` is off.
- E223: `commit_label_layout: table` in a horizontal orientation.
- E224: `commit_label_layout: table` with explicit `commit_row_mode: shared`.

`theme.orientation` is consulted here for E223 — a feature-support
gate that rejects an unsupported combination, not a geometry decision;
the layout/state orientation-blind invariant binds the geometry stages,
not this validation pass (see `docs/architecture.md` invariant 7).
"""

from gitsvg._shared.value_types import CommitLabelLayout, CommitRowMode
from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.theme import Theme
from gitsvg.validate._user_overrides import UserOverrides


def check_resolved_config(theme: Theme, overrides: UserOverrides, report: ValidationReport) -> None:
    """Emit the resolved-config conflict errors (E221-E224).

    Args:
        theme: The fully-resolved theme.
        overrides: What the input explicitly set (the `UserOverrides` record).
        report: Receives any conflict errors.
    """
    _check_branch_pos_conflicts(theme, overrides, report)
    _check_merge_lane_clearance_conflict(theme, overrides, report)
    _check_table_mode_conflicts(theme, overrides, report)


def _check_branch_pos_conflicts(theme: Theme, overrides: UserOverrides, report: ValidationReport) -> None:
    """Emit E221 for each `branch_pos` pin when `auto_lane_change` is on.

    A pin fixes a branch's lane for life; `auto_lane_change` keeps lanes
    free to migrate. The two are mutually exclusive.
    """
    if not theme.auto_lane_change:
        return
    for pin in overrides.branch_pins:
        report.add(
            ValidationError(
                file=pin.file,
                line=pin.line,
                code="E221",
                message=(
                    f"branch {pin.name!r} sets branch_pos, which conflicts with "
                    f"theme.auto_lane_change (a pinned lane cannot also migrate)"
                ),
                field="branch_pos",
            )
        )


def _check_merge_lane_clearance_conflict(theme: Theme, overrides: UserOverrides, report: ValidationReport) -> None:
    """Emit E222 when `merge_lane_clearance` is set while `auto_lane_change` is off.

    `merge_lane_clearance` only governs how a migrating sibling repacks
    around a merged source's reserved lane — machinery the flag-off path
    never runs. An explicit value under a disabled flag is therefore dead
    config and is rejected rather than silently ignored.

    The trigger is presence in `overrides` — the user set the field, which
    is the mistake even at its default `1`. A named-theme switch that wipes
    prior overrides clears the field from the record first, so switching
    themes is the documented escape hatch.
    """
    if theme.auto_lane_change:
        return
    entry = overrides.theme_fields.get("merge_lane_clearance")
    if entry is None:
        return
    report.add(
        ValidationError(
            file=entry.file,
            line=entry.line,
            code="E222",
            message=(
                "theme.merge_lane_clearance has no effect unless theme.auto_lane_change "
                "is enabled (enable auto_lane_change or drop merge_lane_clearance)"
            ),
            field="merge_lane_clearance",
        )
    )


def _check_table_mode_conflicts(theme: Theme, overrides: UserOverrides, report: ValidationReport) -> None:
    """Emit the table-mode mutual-exclusion errors (E223, E224).

    `commit_label_layout: table` lays commit metadata out as a column
    table beside the graph — a layout only the vertical orientations
    support, and one that needs exactly one commit per row. So table mode
    conflicts with a horizontal orientation (E223) and with an explicit
    `commit_row_mode: shared` (E224). Both check the resolved theme, so a
    later named-theme switch that drops table mode clears the conflict.

    `split()` already forces `commit_row_mode → unique` under table mode,
    so E224 fires only when the user *explicitly* set `shared` — the
    contradiction is the mistake, not the (silently honored) unset case.
    """
    if theme.commit_label_layout != CommitLabelLayout.TABLE:
        return

    if not theme.orientation.is_vertical:
        entry = overrides.theme_fields.get("commit_label_layout")
        file, line = (entry.file, entry.line) if entry else (None, 0)
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E223",
                message=(
                    "theme.commit_label_layout 'table' is supported only in vertical orientations "
                    f"(got {theme.orientation.value!r}); use a vertical orientation or 'inline' labels"
                ),
                field="commit_label_layout",
            )
        )

    row_mode = overrides.theme_fields.get("commit_row_mode")
    if row_mode is not None and row_mode.value == CommitRowMode.SHARED:
        report.add(
            ValidationError(
                file=row_mode.file,
                line=row_mode.line,
                code="E224",
                message=(
                    "theme.commit_row_mode 'shared' conflicts with commit_label_layout 'table' "
                    "(table mode lays one commit per row); drop commit_row_mode or set it to 'unique'"
                ),
                field="commit_row_mode",
            )
        )
