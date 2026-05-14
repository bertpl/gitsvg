"""Shared helpers for state-engine tests."""

from gitsvg.errors import ValidationReport
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import State, apply_ops


def build_state_from_jsonl(jsonl: str) -> tuple[State, ValidationReport]:
    """Build a fresh state from the given JSONL text and return `(state, report)`.

    Runs the same parse + apply pipeline as the validate CLI (minus
    import resolution and the end-of-file check), starting from an
    empty state. The report holds parser errors and semantic errors
    combined, so a test can assert clean or inspect the full set
    without juggling two reports.
    """
    parsed, report = parse_jsonl_text(jsonl, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    return state, report
