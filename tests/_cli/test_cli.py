"""Top-level CLI tests."""

from click.testing import CliRunner

from gitsvg import __version__
from gitsvg._cli._cli import cli


def test_version_flag() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["--version"])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help_lists_schema_and_errors_subcommands() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["--help"])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert "schema" in result.output
    assert "errors" in result.output
