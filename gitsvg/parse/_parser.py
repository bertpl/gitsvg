"""JSONL parser for gitsvg input files.

Reads a `.gitsvg.jsonl` file (or in-memory text) line by line, parses each
non-empty line as JSON, dispatches to the right pydantic op model via the
`op:` discriminator, and accumulates errors — each carrying `(file, line,
field, code, message)` — into a `ValidationReport`.

The parser does not raise — it accumulates. A line that fails one phase is
skipped, but the parser continues to the next line so the agent gets the
full picture in one run.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import OP_ADAPTER, OP_NAMES

from ._parsed_op import ParsedOp


# ==================================================================================================
#  Public API
# ==================================================================================================
def parse_jsonl_file(path: Path) -> tuple[list[ParsedOp], ValidationReport]:
    """Parse a `.gitsvg.jsonl` file and schema-validate every op.

    Args:
        path: Path to the JSONL file.

    Returns:
        A tuple `(parsed_ops, report)`. `parsed_ops` contains one
        `ParsedOp` per successfully validated line, in source order.
        `report` accumulates errors from all failed lines; an empty
        report means every line validated.
    """
    text = path.read_text(encoding="utf-8")
    return parse_jsonl_text(text, file=str(path))


def parse_jsonl_text(text: str, *, file: str = "<input>") -> tuple[list[ParsedOp], ValidationReport]:
    """Parse JSONL text and schema-validate every op.

    Args:
        text: The full JSONL content.
        file: Logical file path used for error reporting. Tests pass
            an arbitrary label; production callers pass the real path.

    Returns:
        A tuple `(parsed_ops, report)` — see `parse_jsonl_file`.
    """
    parsed_ops: list[ParsedOp] = []
    report = ValidationReport()

    for line_no, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        result = _parse_one_line(raw, file=file, line=line_no)
        if isinstance(result, ParsedOp):
            parsed_ops.append(result)
        else:
            for err in result:
                report.add(err)

    return parsed_ops, report


# ==================================================================================================
#  Per-line parsing
# ==================================================================================================
def _parse_one_line(raw: str, *, file: str, line: int) -> ParsedOp | list[ValidationError]:
    """Parse a single non-empty line into a `ParsedOp` or a list of errors.

    Args:
        raw: The raw line text (already known to be non-empty).
        file: Source file path for error reporting.
        line: 1-based line number for error reporting.

    Returns:
        A `ParsedOp` if the line is fully valid, or a list of one or
        more `ValidationError` records describing what's wrong.
    """
    # --- JSON parse phase -----------------------
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [
            ValidationError(
                file=file,
                line=line,
                code="E001",
                message=f"invalid JSON: {exc.msg}",
            )
        ]

    # --- Pydantic schema phase -------------------
    try:
        op = OP_ADAPTER.validate_python(value)
    except PydanticValidationError as exc:
        return [_map_pydantic_error(err, file=file, line=line) for err in exc.errors()]

    return ParsedOp(op=op, file=file, line=line)


# ==================================================================================================
#  Pydantic-error → gitsvg-code mapping
# ==================================================================================================
_OP_NAMES_SET = set(OP_NAMES)


_PYDANTIC_TYPE_TO_CODE: dict[str, str] = {
    # Discriminator-level (no specific op selected yet)
    "union_tag_not_found": "E002",
    "union_tag_invalid": "E003",
    "model_attributes_type": "E004",
    # Per-field schema
    "extra_forbidden": "E100",
    "missing": "E101",
    "string_pattern_mismatch": "E104",
    "string_too_short": "E105",
    "too_short": "E106",
    "value_error": "E107",
    "literal_error": "E108",
    "enum": "E108",
}


# Numeric range constraints emit names that end in these comparators.
_NUMERIC_RANGE_TYPES = frozenset(
    {
        "greater_than",
        "greater_than_equal",
        "less_than",
        "less_than_equal",
        "multiple_of",
        "finite_number",
    }
)


def _map_pydantic_error(err: Mapping[str, Any], *, file: str, line: int) -> ValidationError:
    """Map a single pydantic error dict to a gitsvg `ValidationError`.

    Args:
        err: One element from `PydanticValidationError.errors()`.
        file: Source file path for error reporting.
        line: 1-based line number for error reporting.

    Returns:
        A `ValidationError` whose `code` matches the pydantic error
        type and whose `field` is the field path with the discriminator
        op name stripped.
    """
    err_type = err["type"]
    code = _resolve_code(err_type)
    field = _normalize_field_path(err["loc"])
    return ValidationError(file=file, line=line, code=code, message=err["msg"], field=field)


def _resolve_code(err_type: str) -> str:
    """Resolve a pydantic error type string to a gitsvg error code.

    Args:
        err_type: The `type` field from a pydantic error dict.

    Returns:
        The corresponding gitsvg code. Known numeric-comparator types
        map to `"E103"` (numeric range); every other type — including
        pydantic's many `_type` / `_parsing` variants and any unknown
        type — falls back to `"E102"` (wrong type), where the catalog
        message still surfaces the pydantic detail.
    """
    if err_type in _PYDANTIC_TYPE_TO_CODE:
        return _PYDANTIC_TYPE_TO_CODE[err_type]
    if err_type in _NUMERIC_RANGE_TYPES:
        return "E103"
    return "E102"


def _normalize_field_path(loc: tuple) -> str | None:
    """Convert a pydantic `loc` tuple to a dotted field path.

    The first element of `loc` is typically the discriminator value
    (op name) when validation reached the per-op layer. It carries
    no information for the user — they already see `op` on the line —
    so it's stripped.

    Args:
        loc: The `loc` tuple from a pydantic error dict.

    Returns:
        A dotted path like `"gap"` or `"parents.0"`, or `None`
        when the location is empty (top-level errors).
    """
    parts = list(loc)
    if parts and parts[0] in _OP_NAMES_SET:
        parts = parts[1:]
    return ".".join(str(p) for p in parts) if parts else None
