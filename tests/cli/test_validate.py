"""CLI tests for `gitsvg validate`."""

import json
from pathlib import Path

from click.testing import CliRunner

from gitsvg.cli._cli import cli


def _write(path: Path, content: str) -> Path:
    """Write `content` to `path` and return the path."""
    path.write_text(content, encoding="utf-8")
    return path


def test_validate_clean_file_exits_zero(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = _write(
        tmp_path / "ok.jsonl",
        '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "msg": "initial"}\n',
    )
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["validate", str(file)])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert result.output == ""


def test_validate_dirty_file_prints_errors_and_exits_one(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = _write(tmp_path / "bad.jsonl", '{"op": "branch"}\n{"op": "rebase"}\n')
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["validate", str(file)])

    # --- assert -----------------------
    assert result.exit_code == 1
    assert "[E101]" in result.output
    assert "[E003]" in result.output


def test_validate_json_flag_emits_structured_report_with_ok_field(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = _write(tmp_path / "bad.jsonl", '{"op": "branch"}\n')
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["validate", "--json", str(file)])

    # --- assert -----------------------
    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert len(payload["errors"]) == 1
    err = payload["errors"][0]
    assert err["code"] == "E101"
    assert err["field"] == "name"
    assert err["line"] == 1


def test_validate_json_flag_on_clean_file_reports_ok_true(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = _write(tmp_path / "ok.jsonl", '{"op": "branch", "name": "main"}\n')
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["validate", "--json", str(file)])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload == {"ok": True, "errors": []}


def test_validate_missing_file_exits_non_zero() -> None:
    # --- arrange ----------------------
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["validate", "/no/such/file.jsonl"])

    # --- assert -----------------------
    assert result.exit_code != 0
