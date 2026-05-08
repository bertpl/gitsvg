"""Tests for the error code registry (`gitsvg._errors._codes`)."""

import pytest

from gitsvg._errors import ErrorCode, all_codes, get, register


def test_register_adds_entry_to_registry(empty_registry: dict) -> None:
    # --- act --------------------------
    entry = register("E001", "Invalid JSON syntax")

    # --- assert -----------------------
    assert isinstance(entry, ErrorCode)
    assert entry.code == "E001"
    assert entry.summary == "Invalid JSON syntax"
    assert empty_registry["E001"] is entry


def test_register_rejects_duplicate_code(empty_registry: dict) -> None:
    # --- arrange ----------------------
    register("E001", "first registration")

    # --- act / assert -----------------
    with pytest.raises(ValueError, match="already registered"):
        register("E001", "second registration")


def test_get_returns_registered_entry(empty_registry: dict) -> None:
    # --- arrange ----------------------
    register("E210", "replaces rule 3 violated")

    # --- act --------------------------
    entry = get("E210")

    # --- assert -----------------------
    assert entry is not None
    assert entry.code == "E210"


def test_get_returns_none_for_unknown_code(empty_registry: dict) -> None:
    # --- act --------------------------
    entry = get("E999")

    # --- assert -----------------------
    assert entry is None


def test_all_codes_preserves_declaration_order(empty_registry: dict) -> None:
    # --- arrange ----------------------
    register("E300", "import cycle detected")
    register("E001", "invalid JSON")
    register("E210", "replaces rule violated")

    # --- act --------------------------
    codes = [entry.code for entry in all_codes()]

    # --- assert -----------------------
    assert codes == ["E300", "E001", "E210"]


def test_registry_is_empty_in_v0_0_2_pr2(empty_registry: dict) -> None:
    """Reset to the pre-PR2 state — PR2 ships zero codes."""
    # --- act --------------------------
    codes = all_codes()

    # --- assert -----------------------
    assert codes == []
