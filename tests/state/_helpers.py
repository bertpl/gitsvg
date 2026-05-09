"""Shared helpers for state-engine tests."""

from gitsvg.errors import ValidationReport
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import State, apply_ops


def parse_and_apply(jsonl: str) -> tuple[State, ValidationReport]:
    """Parse + apply the given JSONL text and return `(state, report)`.

    The report holds parser errors and semantic errors combined, so a
    test can assert clean or inspect the full set without juggling two
    reports.
    """
    parsed, report = parse_jsonl_text(jsonl, file="x.jsonl")
    state = apply_ops(parsed, report)
    return state, report
