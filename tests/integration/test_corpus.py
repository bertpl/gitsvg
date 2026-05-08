"""Integration tests over the synthetic input corpus.

Walks `tests/fixtures/inputs/` and runs the full validate pipeline
(parse → import-resolve → state-apply → end-of-file check) on each
fixture file. Happy fixtures must validate cleanly. Sad fixtures must
emit at least the expected error code(s) — additional cascading errors
are allowed.
"""

from pathlib import Path

import pytest

from gitsvg.errors import ValidationReport
from gitsvg.imports import resolve_imports
from gitsvg.parse import parse_jsonl_file
from gitsvg.state import apply_ops, check_end_of_file

CORPUS_DIR = Path(__file__).parent.parent / "fixtures" / "inputs"


# ==================================================================================================
#  Pipeline helper
# ==================================================================================================
def _validate(path: Path) -> ValidationReport:
    """Run the full validate pipeline on `path` and return the report."""
    parsed_ops, report = parse_jsonl_file(path)
    expanded = resolve_imports(parsed_ops, file=path, report=report)
    state = apply_ops(expanded, report)
    check_end_of_file(state, report)
    return report


# ==================================================================================================
#  Happy-path fixtures — must validate cleanly
# ==================================================================================================
HAPPY_FIXTURES = [
    "happy_basics.gitsvg.jsonl",
    "happy_squash_and_rebuild.gitsvg.jsonl",
    "happy_import_base.gitsvg.jsonl",
    "happy_import_derived.gitsvg.jsonl",
]


@pytest.mark.parametrize("filename", HAPPY_FIXTURES)
def test_happy_fixture_validates_clean(filename: str) -> None:
    # --- act --------------------------
    report = _validate(CORPUS_DIR / filename)

    # --- assert -----------------------
    assert report.is_clean(), f"{filename}: unexpected errors {[e.format() for e in report.errors]}"


# ==================================================================================================
#  Sad-path fixtures — must emit at least the expected codes
# ==================================================================================================
SAD_FIXTURES: list[tuple[str, set[str]]] = [
    ("bad_parse_invalid_json.gitsvg.jsonl", {"E001"}),
    ("bad_parse_unknown_op.gitsvg.jsonl", {"E003"}),
    ("bad_shape_violations.gitsvg.jsonl", {"E101", "E104", "E108"}),
    ("bad_semantic_undefined.gitsvg.jsonl", {"E200", "E201"}),
    ("bad_semantic_kind_mismatch.gitsvg.jsonl", {"E200"}),
    ("bad_replaces_non_contiguous.gitsvg.jsonl", {"E206"}),
    ("bad_eof_dangling.gitsvg.jsonl", {"E400", "E401"}),
    ("bad_import_cycle_a.gitsvg.jsonl", {"E300"}),
    ("bad_import_missing.gitsvg.jsonl", {"E302"}),
]


@pytest.mark.parametrize("filename, expected_codes", SAD_FIXTURES)
def test_sad_fixture_emits_expected_codes(filename: str, expected_codes: set[str]) -> None:
    # --- act --------------------------
    report = _validate(CORPUS_DIR / filename)

    # --- assert -----------------------
    actual = {e.code for e in report.errors}
    missing = expected_codes - actual
    assert not missing, f"{filename}: missing expected codes {missing}, got {actual}"


def test_kind_mismatch_message_includes_hint() -> None:
    """The kind-typed hint ('did you mean from_commit?') should fire on this fixture."""
    # --- act --------------------------
    report = _validate(CORPUS_DIR / "bad_semantic_kind_mismatch.gitsvg.jsonl")

    # --- assert -----------------------
    assert any("from_commit" in e.message for e in report.errors)
