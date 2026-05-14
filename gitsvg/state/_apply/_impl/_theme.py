"""Apply a `theme` op to state — patch the live theme per the cascade rule."""

import copy
from typing import cast

from gitsvg._theme import DEFAULT_THEME
from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import ThemeOp
from gitsvg.parse import ParsedOp
from gitsvg.state._state import State

# ==================================================================================================
#  Named-theme registry
# ==================================================================================================
# Built-in named themes the user can select with `{"op": "theme", "name": "..."}`.
# Setting a name replaces every theme field with that theme's values before any
# explicit overrides on the same op apply. Only `"default"` exists today; richer
# named themes ship in a later version. New entries land here, no other change
# needed.
NAMED_THEMES = {
    "default": DEFAULT_THEME,
}


# ==================================================================================================
#  Apply
# ==================================================================================================
# Fields a `theme:` op carries that aren't theme fields themselves; excluded
# when copying the op onto state.theme.
_NON_THEME_FIELDS = frozenset({"op", "name"})

# Fields with constraints beyond what `NonNegativeFloat` / `NonNegativeInt`
# already enforce. Each entry maps a field name to a (predicate, error_code,
# message_suffix) triple. The predicate returns True when the value is
# *acceptable*; failure emits the error code with a message of the form
# `{field} {message_suffix} (got {value})`.
_FIELD_CONSTRAINTS: dict[str, tuple] = {
    # Spacings — zero collapses lanes / rows onto themselves.
    "branch_spacing": (lambda v: v > 0, "E218", "must be > 0"),
    "commit_spacing": (lambda v: v > 0, "E218", "must be > 0"),
    # Font sizes — zero makes text invisible.
    "label_font_size": (lambda v: v > 0, "E219", "must be > 0"),
    "branch_label_font_size": (lambda v: v > 0, "E219", "must be > 0"),
    "hash_font_size": (lambda v: v > 0, "E219", "must be > 0"),
}


def apply_theme_op(state: State, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `theme` op.

    Cascade:

    1. If `name` is set, replace every field on `state.theme` with the
       named theme's values. Unknown name → E216, no other change.
    2. For every explicit field present in the op (other than `name`),
       assign it onto `state.theme` — overrides any prior value
       (including any set by step 1).

    An op carrying neither `name` nor any explicit override is rejected
    with E217.

    Args:
        state: The state to mutate.
        parsed: The validated parsed op record.
        report: Receives semantic errors.
    """
    op = cast(ThemeOp, parsed.op)
    file = parsed.file
    line = parsed.line

    explicit_fields = op.model_fields_set - _NON_THEME_FIELDS
    has_name = "name" in op.model_fields_set

    # --- Empty-op rejection -------------------
    if not has_name and not explicit_fields:
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E217",
                message="theme op must set 'name' or at least one explicit field",
            )
        )
        return

    # --- Step 1: named theme replaces all -----
    if has_name:
        named = NAMED_THEMES.get(op.name)
        if named is None:
            known = ", ".join(sorted(NAMED_THEMES))
            report.add(
                ValidationError(
                    file=file,
                    line=line,
                    code="E216",
                    message=f"unknown theme name {op.name!r} (known: {known})",
                    field="name",
                )
            )
            return
        state.theme = copy.deepcopy(named)

    # --- Step 2: explicit overrides on top ----
    # Deep-copy each value so mutable fields (e.g. `colors` dict) on
    # state.theme don't alias back to the op model. Fields that fail
    # their semantic constraint emit an error but don't block the
    # other fields from applying.
    for name in explicit_fields:
        value = getattr(op, name)
        constraint = _FIELD_CONSTRAINTS.get(name)
        if constraint is not None:
            predicate, code, message_suffix = constraint
            if not predicate(value):
                report.add(
                    ValidationError(
                        file=file,
                        line=line,
                        code=code,
                        message=f"{name} {message_suffix} (got {value})",
                        field=name,
                    )
                )
                continue
        setattr(state.theme, name, copy.deepcopy(value))
