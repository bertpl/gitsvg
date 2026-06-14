"""CLI tests for `gitsvg validate`."""

import json
from pathlib import Path

from click.testing import CliRunner

from gitsvg.cli._cli import cli
from tests._jsonl import build_jsonl


def _write(path: Path, content: str) -> Path:
    """Write `content` to `path` and return the path."""
    path.write_text(content, encoding="utf-8")
    return path


def test_validate_clean_file_exits_zero(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = _write(
        tmp_path / "ok.jsonl",
        build_jsonl({"op": "branch", "name": "main"}, {"op": "commit", "branch": "main", "msg": "initial"}),
    )
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["validate", str(file)])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert result.output == ""


def test_validate_dirty_file_prints_errors_and_exits_one(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = _write(tmp_path / "bad.jsonl", build_jsonl({"op": "branch"}, {"op": "rebase"}))
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["validate", str(file)])

    # --- assert -----------------------
    assert result.exit_code == 1
    assert "[E101]" in result.output
    assert "[E003]" in result.output


def test_validate_json_flag_emits_structured_report_with_ok_field(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = _write(tmp_path / "bad.jsonl", build_jsonl({"op": "branch"}))
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
    file = _write(tmp_path / "ok.jsonl", build_jsonl({"op": "branch", "name": "main"}))
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


def test_validate_resolves_import_chain(tmp_path: Path) -> None:
    """Import resolution flows through the validate pipeline end-to-end."""
    # --- arrange ----------------------
    base = _write(
        tmp_path / "base.jsonl",
        build_jsonl({"op": "branch", "name": "main"}, {"op": "commit", "branch": "main", "id": "c1", "msg": "x"}),
    )
    derived = _write(
        tmp_path / "derived.jsonl",
        build_jsonl({"op": "import", "path": f"./{base.name}"}, {"op": "highlight", "commit": "c1"}),
    )
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["validate", str(derived)])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert result.output == ""


def test_validate_flags_eof_dangling_reference(tmp_path: Path) -> None:
    """End-of-file checks flow through the validate pipeline end-to-end."""
    # --- arrange ----------------------
    file = _write(
        tmp_path / "dangling.jsonl",
        (
            build_jsonl(
                {"op": "branch", "name": "main"},
                {"op": "commit", "branch": "main", "id": "c1", "msg": "x"},
                {"op": "branch", "name": "feat", "from_commit": "c1"},
                {"op": "remove", "commits": ["c1"]},
            )
        ),
    )
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["validate", str(file)])

    # --- assert -----------------------
    assert result.exit_code == 1
    assert "[E400]" in result.output
