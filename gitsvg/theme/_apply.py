"""Apply a `theme` op to a `ThemeBuilder` — accumulate user overrides + handle name resets."""

import copy
from typing import cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import ThemeOp
from gitsvg.parse import ParsedOp
from gitsvg.state._state import State
from gitsvg.theme._builder import ThemeBuilder
from gitsvg.theme._default_theme import DefaultTheme
from gitsvg.theme._theme import Theme

# ==================================================================================================
#  Named-theme registry
# ==================================================================================================
# Built-in named themes the user can select with `{"op": "theme", "name": "..."}`.
# Setting a name swaps the `ThemeBuilder.theme_cls` to the named subclass and
# discards any explicit fields accumulated so far. Only `"default"` exists
# today; richer named themes ship in a later version. New entries land here;
# no other change needed.
NAMED_THEMES: dict[str, type[Theme]] = {
    "default": DefaultTheme,
}


# ==================================================================================================
#  Apply
# ==================================================================================================
# Fields a `theme:` op carries that aren't theme fields themselves; excluded
# when copying the op into the builder's `user_set` dict.
_NON_THEME_FIELDS = frozenset({"op", "name"})

# Fields with constraints beyond what `NonNegativeFloat` / `NonNegativeInt`
# already enforce. Each entry maps a field name to a (predicate, error_code,
# message_suffix) triple. The predicate returns True when the value is
# *acceptable*; failure emits the error code with a message of the form
# `{field} {message_suffix} (got {value})`. The same invariants also live on
# `Theme` as per-field validators (defence in depth at `build()` time); the
# explicit checks here surface line numbers via the validation report.
_FIELD_CONSTRAINTS: dict[str, tuple] = {
    # Spacings — zero collapses lanes / rows onto themselves.
    "branch_spacing": (lambda v: v > 0, "E218", "must be > 0"),
    "commit_spacing": (lambda v: v > 0, "E218", "must be > 0"),
    # Font sizes — zero makes text invisible.
    "label_font_size": (lambda v: v > 0, "E219", "must be > 0"),
    "branch_label_font_size": (lambda v: v > 0, "E219", "must be > 0"),
    "hash_font_size": (lambda v: v > 0, "E219", "must be > 0"),
}


def apply_theme_op(state: State, builder: ThemeBuilder, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `theme` op by mutating the `ThemeBuilder`.

    Cascade:

    1. If `name` is set, swap `builder.theme_cls` to the named subclass
       and discard any previously-accumulated `user_set`. Unknown name →
       E216, no other change.
    2. For every explicit field present in the op (other than `name`),
       merge it into `builder.user_set` — overrides any prior value
       (including any cleared by step 1).

    An op carrying neither `name` nor any explicit override is rejected
    with E217.

    Args:
        state: Unused. Included for the shared apply-handler signature.
        builder: The live `ThemeBuilder` to mutate.
        parsed: The validated parsed op record.
        report: Receives semantic errors.
    """
    del state  # signature uniformity; theme ops don't read or write state
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

    # --- Step 1: named theme reset ------------
    if has_name:
        theme_cls = NAMED_THEMES.get(op.name)
        if theme_cls is None:
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
        builder.reset_to(theme_cls)

    # --- Step 2: accumulate explicit overrides
    # Deep-copy each value so mutable fields (e.g. `colors` dict) in
    # `user_set` don't alias the op model. Fields that fail their
    # semantic constraint emit an error but don't block other fields
    # from accumulating.
    #
    # Explicit `null` on `orientation` resets to the package default
    # (`Orientation.BT`); we represent that by *omitting* it from
    # `user_set` so the resolver fills it at `build()` time. Other
    # fields with a None-allowed semantic (e.g. `background_color`)
    # accept None as a legitimate user value and enter `user_set`
    # normally.
    for name in explicit_fields:
        value = getattr(op, name)
        if name == "orientation" and value is None:
            builder.user_set.pop("orientation", None)
            continue
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
        builder.user_set[name] = copy.deepcopy(value)
