"""Tests for the `ValidationError` record dataclass."""

import pytest

from gitsvg.errors import ValidationError


def test_format_renders_minimal_error(populated_registry: dict) -> None:
    # --- arrange ----------------------
    err = ValidationError(file="x.jsonl", line=7, code="E999", message="some failure happened")

    # --- act --------------------------
    rendered = err.format()

    # --- assert -----------------------
    assert rendered == "x.jsonl:7: [E999] some failure happened"


def test_format_includes_field_when_set(populated_registry: dict) -> None:
    # --- arrange ----------------------
    err = ValidationError(
        file="x.jsonl",
        line=7,
        code="E998",
        message="missing required field",
        field="branch",
    )

    # --- act --------------------------
    rendered = err.format()

    # --- assert -----------------------
    assert rendered == "x.jsonl:7: [E998] branch: missing required field"


def test_format_omits_location_when_file_is_none(populated_registry: dict) -> None:
    # --- arrange ----------------------
    err = ValidationError(file=None, line=0, code="E999", message="no source location")

    # --- act --------------------------
    rendered = err.format()

    # --- assert -----------------------
    assert rendered == "[E999] no source location"


def test_format_appends_suggestion_as_did_you_mean(populated_registry: dict) -> None:
    # --- arrange ----------------------
    err = ValidationError(
        file="x.jsonl",
        line=7,
        code="E998",
        message="branch 'mian' is not declared",
        field="branch",
        suggestion="main",
    )

    # --- act --------------------------
    rendered = err.format()

    # --- assert -----------------------
    assert rendered == "x.jsonl:7: [E998] branch: branch 'mian' is not declared — did you mean 'main'?"


def test_validation_error_is_frozen_and_hashable(populated_registry: dict) -> None:
    # --- arrange ----------------------
    err = ValidationError(file="x.jsonl", line=1, code="E999", message="msg")

    # --- act / assert -----------------
    assert hash(err) == hash(err)


def test_construction_rejects_unregistered_code(populated_registry: dict) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="not in the catalog"):
        ValidationError(file="x.jsonl", line=1, code="E000", message="unknown code")


def test_construction_rejects_unregistered_code_under_empty_registry(empty_registry: dict) -> None:
    """With an empty catalog, every code is unregistered and construction must fail."""
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="not in the catalog"):
        ValidationError(file="x.jsonl", line=1, code="E001", message="msg")
