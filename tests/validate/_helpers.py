"""Shared helpers for validate-stage tests."""

from gitsvg.errors import ValidationReport
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import ThemeBuilder
from gitsvg.validate import UserOverrides, check_resolved_config


def resolved_config_report(jsonl: str) -> ValidationReport:
    """Parse + apply `jsonl`, then run the resolved-config checks; return the report.

    Mirrors the validate pipeline's config-conflict path (E221-E224) on
    in-memory text: the report holds parser, semantic, and config-conflict
    errors combined, so a test can assert clean or inspect the full set.
    """
    parsed, report = parse_jsonl_text(jsonl, file="x.jsonl")
    builder = ThemeBuilder()
    state, theme = apply_ops(parsed, report, builder=builder)
    overrides = UserOverrides.collect(state, builder)
    check_resolved_config(theme, overrides, report)
    return report
