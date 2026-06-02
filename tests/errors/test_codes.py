"""Tests for the catalog-driven code registry (`gitsvg.errors._codes`)."""

from pathlib import Path

import pytest

from gitsvg.errors import ErrorCode, _codes, all_codes, find_error_code


# ==================================================================================================
#  _scan_catalog
# ==================================================================================================
def test_scan_catalog_empty_dir_returns_empty_dict(tmp_path: Path) -> None:
    # --- act --------------------------
    result = _codes._scan_catalog(tmp_path)

    # --- assert -----------------------
    assert result == {}


def test_scan_catalog_loads_one_entry_per_code_md_file(fixtures_catalog_dir: Path) -> None:
    # --- act --------------------------
    result = _codes._scan_catalog(fixtures_catalog_dir)

    # --- assert -----------------------
    assert "E998" in result
    assert "E999" in result
    assert isinstance(result["E999"], ErrorCode)


def test_scan_catalog_extracts_summary_from_h1_heading(fixtures_catalog_dir: Path) -> None:
    # --- act --------------------------
    result = _codes._scan_catalog(fixtures_catalog_dir)

    # --- assert -----------------------
    assert result["E999"].summary == "test fixture"
    assert result["E998"].summary == "second test fixture"


def test_scan_catalog_skips_files_not_matching_code_filename_pattern(tmp_path: Path) -> None:
    # --- arrange ----------------------
    (tmp_path / "E001.md").write_text("# E001 - ok")
    (tmp_path / "README.md").write_text("# Some readme")
    (tmp_path / "notes.md").write_text("# Notes")
    (tmp_path / "E1.md").write_text("# E1 - too short")

    # --- act --------------------------
    result = _codes._scan_catalog(tmp_path)

    # --- assert -----------------------
    assert list(result.keys()) == ["E001"]


def test_scan_catalog_returns_codes_in_sorted_order(tmp_path: Path) -> None:
    # --- arrange ----------------------
    (tmp_path / "E300.md").write_text("# E300 - third")
    (tmp_path / "E001.md").write_text("# E001 - first")
    (tmp_path / "E100.md").write_text("# E100 - second")

    # --- act --------------------------
    codes = list(_codes._scan_catalog(tmp_path).keys())

    # --- assert -----------------------
    assert codes == ["E001", "E100", "E300"]


# ==================================================================================================
#  _extract_summary
# ==================================================================================================
@pytest.mark.parametrize(
    ("heading", "code", "expected"),
    [
        ("# E001 - Invalid JSON\n\nMore text.\n", "E001", "Invalid JSON"),
        ("# E210: replaces rule violated\n", "E210", "replaces rule violated"),
        ("# Whatever heading text\n", "E001", "Whatever heading text"),
        ("Just a paragraph.\n", "E001", ""),
        # First non-blank line is an H2; the H1 convention is violated, so return empty.
        ("## Cause\n\n# E001 - title\n", "E001", ""),
    ],
    ids=[
        "dash-separator",
        "colon-separator",
        "no-separator-falls-back-to-full-heading",
        "no-h1-returns-empty",
        "h2-first-returns-empty",
    ],
)
def test_extract_summary(heading: str, code: str, expected: str) -> None:
    # --- act --------------------------
    summary = _codes._extract_summary(heading, code)

    # --- assert -----------------------
    assert summary == expected


# ==================================================================================================
#  Registry public API (find_error_code / all_codes)
# ==================================================================================================
def test_find_error_code_returns_registered_entry(populated_registry: dict) -> None:
    # --- act --------------------------
    entry = find_error_code("E999")

    # --- assert -----------------------
    assert entry is not None
    assert entry.code == "E999"


def test_find_error_code_returns_none_for_unknown_code(populated_registry: dict) -> None:
    # --- act --------------------------
    entry = find_error_code("E000")

    # --- assert -----------------------
    assert entry is None


def test_all_codes_returns_sorted_entries(populated_registry: dict) -> None:
    # --- act --------------------------
    codes = [entry.code for entry in all_codes()]

    # --- assert -----------------------
    assert codes == ["E998", "E999"]


def test_production_registry_includes_parser_and_schema_codes() -> None:
    """The production catalog declares the parse-phase and schema-phase codes."""
    # --- act --------------------------
    codes = {entry.code for entry in all_codes()}

    # --- assert -----------------------
    assert {"E001", "E002", "E003", "E004"}.issubset(codes)
    assert {"E100", "E101", "E102", "E103", "E104", "E105", "E106", "E107", "E108"}.issubset(codes)
