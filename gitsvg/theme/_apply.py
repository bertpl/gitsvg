"""Apply a `theme` op to a `ThemeBuilder` — drive the per-op cascade."""

import copy
from typing import cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import ThemeOp
from gitsvg.parse import ParsedOp
from gitsvg.state._state import State
from gitsvg.theme._builder import ThemeBuilder
from gitsvg.theme._default_theme import DefaultTheme
from gitsvg.theme._theme import Theme
from gitsvg.theme.themes import CompactTheme, DarkTheme, MutedTheme

# ==================================================================================================
#  Named-theme registry
# ==================================================================================================
# Built-in named themes the user can select with `{"op": "theme", "name": "..."}`.
# Setting a name swaps the `ThemeBuilder.theme_cls` to the named subclass; the
# subsequent wipe of accumulated overrides is conditional on the op's
# `keep_prior_overrides` flag (default `False` = wipe, matching v0.1.4's
# documented `{name: "default"}` behaviour). New entries land here; no other
# change needed.
NAMED_THEMES: dict[str, type[Theme]] = {
    "default": DefaultTheme,
    "muted": MutedTheme,
    "dark": DarkTheme,
    "compact": CompactTheme,
}


# ==================================================================================================
#  Apply
# ==================================================================================================
# Fields a `theme:` op carries that aren't theme-field overrides; excluded
# when copying the op into the builder's `user_set` dict. `name` and
# `keep_prior_overrides` drive the cascade itself and are handled separately.
_NON_THEME_FIELDS = frozenset({"op", "name", "keep_prior_overrides"})

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

    Cascade rules:

    1. The op is rejected as empty (E217) when it carries no `name`,
       no `keep_prior_overrides`, and no explicit theme fields.
    2. Explicit `keep_prior_overrides` without `name` is rejected
       (E220) — the flag has no meaningful effect there. The rest of
       the op (other valid fields) still applies.
    3. When `name` is set, `builder.theme_cls` is reassigned to the
       named subclass. Unknown name → E216 and the rest of the op is
       skipped. When the name is known and `keep_prior_overrides` is
       `False` (its default), `builder.clear_overrides()` wipes both
       prior `user_set` and `branch_color_overrides`.
    4. Every explicit theme field on the op (i.e. fields other than
       `name` and `keep_prior_overrides`) merges into `user_set`,
       overriding any prior value — including any cleared by step 3.

    The wipe in step 3 runs before the current op's own fields apply
    in step 4, so a mixed op like `{name: dark, commit_radius: 8}`
    always produces dark + commit_radius=8 — never plain dark.

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

    fields_set = op.model_fields_set
    has_name = "name" in fields_set
    has_flag = "keep_prior_overrides" in fields_set
    explicit_fields = fields_set - _NON_THEME_FIELDS

    # --- Empty-op rejection -------------------
    if not has_name and not has_flag and not explicit_fields:
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E217",
                message="theme op must set 'name', at least one explicit field, or both",
            )
        )
        return

    # --- Flag-without-name rejection ----------
    # Doesn't return — other valid fields in the same op still apply,
    # matching the partial-application pattern for E218 / E219.
    if has_flag and not has_name:
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E220",
                message="keep_prior_overrides may only be set on a theme op that also sets 'name'",
                field="keep_prior_overrides",
            )
        )

    # --- Step 1: named-theme switch -----------
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
        builder.set_theme_cls(theme_cls)
        if not op.keep_prior_overrides:
            builder.clear_overrides()

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
