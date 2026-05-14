"""CLI tests for `gitsvg schema`."""

import json

from click.testing import CliRunner

from gitsvg.cli._cli import cli


def test_schema_no_args_prints_index_with_all_op_names() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema"])

    # --- assert -----------------------
    assert result.exit_code == 0
    for op_name in ["import", "grid", "branch", "commit", "merge", "pull_request", "remove", "highlight"]:
        assert op_name in result.output
    assert "File-level constraints" in result.output


def test_schema_with_op_name_prints_valid_json_schema() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "commit"])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["type"] == "object"
    assert "branch" in payload["properties"]


def test_schema_list_ops_prints_bare_names_one_per_line() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "--list-ops"])

    # --- assert -----------------------
    assert result.exit_code == 0
    lines = [line for line in result.output.splitlines() if line]
    assert lines == [
        "import",
        "grid",
        "theme",
        "branch",
        "commit",
        "merge",
        "pull_request",
        "remove",
        "highlight",
    ]


def test_schema_unknown_op_exits_non_zero() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["schema", "rebase"])

    # --- assert -----------------------
    assert result.exit_code != 0
    assert "Unknown op" in result.output
