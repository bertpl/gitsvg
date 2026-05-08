"""Tests for the `ValidationError` record dataclass."""

from gitsvg._errors import ValidationError


def test_format_renders_minimal_error() -> None:
    # --- arrange ----------------------
    err = ValidationError(file="x.jsonl", line=7, code="E210", message="replaces rule 3 violated")

    # --- act --------------------------
    rendered = err.format()

    # --- assert -----------------------
    assert rendered == "x.jsonl:7: [E210] replaces rule 3 violated"


def test_format_includes_field_when_set() -> None:
    # --- arrange ----------------------
    err = ValidationError(
        file="x.jsonl",
        line=7,
        code="E110",
        message="missing required field",
        field="branch",
    )

    # --- act --------------------------
    rendered = err.format()

    # --- assert -----------------------
    assert rendered == "x.jsonl:7: [E110] branch: missing required field"


def test_validation_error_is_frozen_and_hashable() -> None:
    # --- arrange ----------------------
    err = ValidationError(file="x.jsonl", line=1, code="E001", message="invalid JSON")

    # --- act / assert -----------------
    assert hash(err) == hash(err)
