"""Shared validate-pipeline helper for the CLI subcommands.

Every command that consumes a `.gitsvg.jsonl` input file (`render`,
`validate`, and the introspection commands) runs the same upfront
sequence: parse → import resolution → per-op state apply →
cross-cutting validation. This module centralises that body so the
subcommands stay focused on what happens *after* the pipeline (write
SVG, emit JSON, etc.).
"""

from pathlib import Path

from gitsvg.errors import ValidationReport
from gitsvg.imports import resolve_imports
from gitsvg.parse import ParsedOp, parse_jsonl_file
from gitsvg.state import State, apply_ops
from gitsvg.theme import Theme, ThemeBuilder
from gitsvg.validate import UserOverrides, check_cross_reference, check_resolved_config


def apply_and_validate(parsed_ops: list[ParsedOp], report: ValidationReport) -> tuple[State, Theme]:
    """Apply ops, then run the cross-cutting end-of-stream validation.

    The post-parse half of the validate pipeline: applies the ops to a
    fresh state and theme, then runs the two validation passes that need
    the fully-applied result — resolved-config conflicts (on the theme +
    the `UserOverrides` record) and dangling cross-references (on the
    state graph).

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


def run_validate_pipeline(input_path: Path) -> tuple[State, ValidationReport, Theme]:
    """Run parse → imports → state-apply → validation on a file.

    Args:
        input_path: Path to a `.gitsvg.jsonl` input file.

    Returns:
        Tuple `(state, report, theme)`. Callers inspect
        `report.is_clean()` to decide whether to proceed to layout /
        render / introspection, or surface the errors and exit
        non-zero.
    """
    parsed_ops, report = parse_jsonl_file(input_path)
    expanded_ops = resolve_imports(parsed_ops, file=input_path, report=report)
    state, theme = apply_and_validate(expanded_ops, report)
    return state, report, theme
