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
    for name in explicit_fields:
        setattr(state.theme, name, getattr(op, name))
