"""CLI tests for `gitsvg errors`."""

from click.testing import CliRunner

from gitsvg._cli._cli import cli


def test_errors_no_args_with_empty_registry_shows_placeholder(empty_registry: dict) -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["errors"])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert "(no error codes registered yet)" in result.output


def test_errors_no_args_with_populated_registry_shows_index(populated_registry: dict) -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["errors"])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert "E998" in result.output
    assert "second test fixture" in result.output
    assert "E999" in result.output
    assert "test fixture" in result.output


def test_errors_list_codes_prints_bare_codes_one_per_line(populated_registry: dict) -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["errors", "--list-codes"])

    # --- assert -----------------------
    assert result.exit_code == 0
    lines = [line for line in result.output.splitlines() if line]
    assert lines == ["E998", "E999"]


def test_errors_with_known_code_prints_catalog_markdown(
    populated_registry: dict,
    monkeypatch,
    fixtures_catalog_dir,
) -> None:
    """The CLI should read the long-form markdown body from the catalog."""
    # --- arrange ----------------------
    # The CLI's load_catalog_entry uses default_catalog_dir() — point that at fixtures.
    from gitsvg._errors import _catalog

    monkeypatch.setattr(_catalog, "default_catalog_dir", lambda: fixtures_catalog_dir)
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["errors", "E999"])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert "# E999 - test fixture" in result.output


def test_errors_with_unknown_code_exits_non_zero(populated_registry: dict) -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["errors", "E000"])

    # --- assert -----------------------
    assert result.exit_code != 0
    assert "Unknown error code" in result.output
