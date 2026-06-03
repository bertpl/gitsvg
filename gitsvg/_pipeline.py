"""Shared post-parse pipeline composition (state-apply + validation).

`apply_and_validate` is the post-parse half of the validate pipeline:
apply the ops to a fresh state and theme, then run the two cross-cutting
validation passes that need the fully-applied result. It lives here —
above both the CLI layer and the public `render_text` entry point — so
neither has to import the other. The CLI's file-based
`run_validate_pipeline` and the public text-based `render_text` both
compose on top of it.
"""

from .errors import ValidationReport
from .parse import ParsedOp
from .state import State, apply_ops
from .theme import Theme, ThemeBuilder
from .validate import UserOverrides, check_cross_reference, check_resolved_config


def apply_and_validate(parsed_ops: list[ParsedOp], report: ValidationReport) -> tuple[State, Theme]:
    """Apply ops, then run the cross-cutting end-of-stream validation.

    Applies the ops to a fresh state and theme, then runs the two
    validation passes that need the fully-applied result —
    resolved-config conflicts (on the theme + the `UserOverrides`
    record) and dangling cross-references (on the state graph).

    Args:
        parsed_ops: Schema-validated ops (imports already resolved).
        report: Report to which semantic and validation errors are appended.

    Returns:
        `(state, theme)` — the fully-applied state and resolved theme.
    """
    builder = ThemeBuilder()
    state, theme = apply_ops(parsed_ops, report, builder=builder)
    overrides = UserOverrides.collect(state, builder)
    check_resolved_config(theme, overrides, report)
    check_cross_reference(state, report)
    return state, theme
