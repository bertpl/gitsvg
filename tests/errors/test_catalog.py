"""Tests for the catalog markdown loader."""

from pathlib import Path

from gitsvg.errors import default_catalog_dir, load_catalog_entry


def test_loads_existing_entry_from_fixture_dir(fixtures_catalog_dir: Path) -> None:
    # --- act --------------------------
    body = load_catalog_entry("E999", catalog_dir=fixtures_catalog_dir)

    # --- assert -----------------------
    assert body is not None
    assert body.startswith("# E999 - test fixture")


def test_returns_none_for_missing_entry(fixtures_catalog_dir: Path) -> None:
    # --- act --------------------------
    body = load_catalog_entry("E000", catalog_dir=fixtures_catalog_dir)

    # --- assert -----------------------
    assert body is None


def test_default_catalog_dir_resolves_to_package_subdir() -> None:
    # --- act --------------------------
    catalog = default_catalog_dir()

    # --- assert -----------------------
    assert catalog is not None


def test_production_catalog_is_empty_in_v0_0_2_pr2() -> None:
    """PR2 ships zero catalog entries; the directory should contain no `.md` files."""
    # --- arrange ----------------------
    catalog = default_catalog_dir()

    # --- act --------------------------
    md_entries = [item.name for item in catalog.iterdir() if item.name.endswith(".md")]

    # --- assert -----------------------
    assert md_entries == []
