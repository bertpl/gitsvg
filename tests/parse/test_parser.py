"""Tests for the JSONL parser and the pydantic-error → gitsvg-code mapping."""

from pathlib import Path

import pytest

from gitsvg.file_format.ops import BranchOp, CommitOp
from gitsvg.parse import ParsedOp, parse_jsonl_file, parse_jsonl_text


# ==================================================================================================
#  Happy path
# ==================================================================================================
def test_parse_empty_text_returns_empty() -> None:
    # --- act --------------------------
    parsed, report = parse_jsonl_text("")

    # --- assert -----------------------
    assert parsed == []
    assert report.is_clean()


def test_parse_skips_blank_and_whitespace_only_lines() -> None:
    # --- arrange ----------------------
    text = '\n   \n{"op": "branch", "name": "main"}\n\n'

    # --- act --------------------------
    parsed, report = parse_jsonl_text(text, file="x.jsonl")

    # --- assert -----------------------
    assert report.is_clean()
    assert len(parsed) == 1
    assert isinstance(parsed[0].op, BranchOp)


def test_parse_attaches_correct_file_and_line_to_each_op() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n\n{"op": "commit", "branch": "main", "msg": "initial"}\n'

    # --- act --------------------------
    parsed, report = parse_jsonl_text(text, file="x.jsonl")

    # --- assert -----------------------
    assert report.is_clean()
    assert [(p.file, p.line, type(p.op)) for p in parsed] == [
        ("x.jsonl", 1, BranchOp),
        ("x.jsonl", 3, CommitOp),
    ]


def test_parse_jsonl_file_reads_from_disk(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = tmp_path / "input.gitsvg.jsonl"
    file.write_text('{"op": "branch", "name": "main"}\n')

    # --- act --------------------------
    parsed, report = parse_jsonl_file(file)

    # --- assert -----------------------
    assert report.is_clean()
    assert len(parsed) == 1
    assert parsed[0].file == str(file)
    assert parsed[0].line == 1


# ==================================================================================================
#  Parse-phase errors (E001-E004)
# ==================================================================================================
def test_invalid_json_emits_e001() -> None:
    # --- act --------------------------
    parsed, report = parse_jsonl_text("{not json}\n", file="x.jsonl")

    # --- assert -----------------------
    assert parsed == []
    assert len(report) == 1
    err = report.errors[0]
    assert err.code == "E001"
    assert err.line == 1


def test_missing_op_field_emits_e002() -> None:
    # --- act --------------------------
    parsed, report = parse_jsonl_text('{"name": "main"}\n', file="x.jsonl")

    # --- assert -----------------------
    assert parsed == []
    assert [e.code for e in report.errors] == ["E002"]


def test_unknown_op_value_emits_e003() -> None:
    # --- act --------------------------
    parsed, report = parse_jsonl_text('{"op": "rebase"}\n', file="x.jsonl")

    # --- assert -----------------------
    assert parsed == []
    assert [e.code for e in report.errors] == ["E003"]


def test_non_object_line_emits_e004() -> None:
    # --- act --------------------------
    parsed, report = parse_jsonl_text("[1, 2, 3]\n", file="x.jsonl")

    # --- assert -----------------------
    assert parsed == []
    assert [e.code for e in report.errors] == ["E004"]


# ==================================================================================================
#  Schema-phase errors (E100-E108)
# ==================================================================================================
@pytest.mark.parametrize(
    "raw, expected_code, expected_field",
    [
        ('{"op": "branch", "name": "main", "unknown": 1}', "E100", "unknown"),
        ('{"op": "branch"}', "E101", "name"),
        ('{"op": "branch", "name": "main", "branch_pos": "x"}', "E102", "branch_pos"),
        ('{"op": "branch", "name": "main", "branch_pos": -1}', "E103", "branch_pos"),
        ('{"op": "branch", "name": "with space"}', "E104", "name"),
        ('{"op": "commit", "branch": "main", "msg": ""}', "E105", "msg"),
        ('{"op": "remove", "commits": []}', "E106", "commits"),
        ('{"op": "commit", "branch": "main"}', "E107", None),
        ('{"op": "branch", "name": "main", "label_side": "top"}', "E108", "label_side"),
    ],
)
def test_shape_errors_map_to_expected_codes(raw: str, expected_code: str, expected_field: str | None) -> None:
    # --- act --------------------------
    parsed, report = parse_jsonl_text(raw + "\n", file="x.jsonl")

    # --- assert -----------------------
    assert parsed == []
    assert len(report) == 1
    err = report.errors[0]
    assert err.code == expected_code
    assert err.field == expected_field
    assert err.line == 1


# ==================================================================================================
#  Mixed input — parser keeps going after errors
# ==================================================================================================
def test_parser_continues_past_errors_to_collect_full_report() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        "{not json}\n"
        '{"op": "commit", "branch": "main", "msg": "initial"}\n'
        '{"op": "branch"}\n'
        '{"op": "highlight", "commit": "c1"}\n'
    )

    # --- act --------------------------
    parsed, report = parse_jsonl_text(text, file="x.jsonl")

    # --- assert -----------------------
    assert [p.line for p in parsed] == [1, 3, 5]
    assert [(e.line, e.code) for e in report.errors] == [(2, "E001"), (4, "E101")]


def test_one_op_can_yield_multiple_shape_errors() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "with space", "branch_pos": -1}\n'

    # --- act --------------------------
    parsed, report = parse_jsonl_text(text, file="x.jsonl")

    # --- assert -----------------------
    assert parsed == []
    codes = sorted(e.code for e in report.errors)
    assert codes == ["E103", "E104"]


# ==================================================================================================
#  ParsedOp dataclass
# ==================================================================================================
def test_parsed_op_is_immutable() -> None:
    # --- arrange ----------------------
    op = BranchOp(op="branch", name="main")
    parsed = ParsedOp(op=op, file="x.jsonl", line=1)

    # --- act / assert -----------------
    with pytest.raises(Exception):
        parsed.line = 2  # type: ignore[misc]
