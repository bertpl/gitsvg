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


def test_render_command_runs() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["render"])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert "not implemented yet" in result.output.lower()
