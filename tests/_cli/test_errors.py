"""CLI tests for `gitsvg errors`."""

import pytest
from click.testing import CliRunner

from gitsvg._cli._cli import cli
from gitsvg._errors import _codes


@pytest.fixture
def empty_registry(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Replace the global error-code registry with an empty dict for the test."""
    fresh: dict = {}
    monkeypatch.setattr(_codes, "_REGISTERED_CODES", fresh)
    return fresh


def test_errors_no_args_with_empty_registry_shows_placeholder() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["errors"])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert "(no error codes registered yet)" in result.output


def test_errors_no_args_with_registered_codes_shows_index(empty_registry: dict) -> None:
    # --- arrange ----------------------
    _codes.register("E001", "Invalid JSON syntax")
    _codes.register("E210", "replaces rule 3 violated")
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["errors"])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert "E001" in result.output
    assert "Invalid JSON syntax" in result.output
    assert "E210" in result.output
    assert "replaces rule 3 violated" in result.output


def test_errors_list_codes_prints_bare_codes_one_per_line(empty_registry: dict) -> None:
    # --- arrange ----------------------
    _codes.register("E001", "first")
    _codes.register("E210", "second")
    _codes.register("E300", "third")
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["errors", "--list-codes"])

    # --- assert -----------------------
    assert result.exit_code == 0
    lines = [line for line in result.output.splitlines() if line]
    assert lines == ["E001", "E210", "E300"]


def test_errors_with_known_code_without_catalog_entry_falls_back_to_summary(
    empty_registry: dict,
) -> None:
    # --- arrange ----------------------
    _codes.register("E001", "Invalid JSON syntax")
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["errors", "E001"])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert "[E001] Invalid JSON syntax" in result.output
    assert "no detailed catalog entry yet" in result.output


def test_errors_with_unknown_code_exits_non_zero(empty_registry: dict) -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["errors", "E999"])

    # --- assert -----------------------
    assert result.exit_code != 0
    assert "Unknown error code" in result.output
