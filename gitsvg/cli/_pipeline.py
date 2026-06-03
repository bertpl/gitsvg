"""Shared file-based validate-pipeline helper for the CLI subcommands.

Every command that consumes a `.gitsvg.jsonl` input file (`render`,
`validate`, and the introspection commands) runs the same upfront
sequence: parse → import resolution → per-op state apply →
cross-cutting validation. This module centralises that body so the
subcommands stay focused on what happens *after* the pipeline (write
SVG, emit JSON, etc.). The post-parse half (`apply_and_validate`) is
shared with the public text entry point and lives in `gitsvg._pipeline`.
"""

from pathlib import Path

from gitsvg._pipeline import apply_and_validate
from gitsvg.errors import ValidationReport
from gitsvg.imports import resolve_imports
from gitsvg.parse import parse_jsonl_file
from gitsvg.state import State
from gitsvg.theme import Theme


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
