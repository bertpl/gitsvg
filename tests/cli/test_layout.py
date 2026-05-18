"""CLI tests for `gitsvg layout`."""

import json
from pathlib import Path

from click.testing import CliRunner

from gitsvg.cli._cli import cli

_OK_JSONL = (
    '{"op": "branch", "name": "main"}\n'
    '{"op": "commit", "branch": "main", "id": "c1", "msg": "first"}\n'
    '{"op": "commit", "branch": "main", "id": "c2", "msg": "second"}\n'
)
_BAD_JSONL = '{"op": "commit", "branch": "main", "msg": "x"}\n'  # main not declared


def _write(path: Path, content: str) -> Path:
    """Write `content` to `path` (creating parents) and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_layout_clean_single_file_emits_json_to_stdout(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_file = _write(tmp_path / "ok.gitsvg.jsonl", _OK_JSONL)
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["layout", str(input_file)])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert set(payload.keys()) == {"grid", "branches", "commits", "arcs", "guides", "pull_requests"}
    assert [c["id"] for c in payload["commits"]] == ["c1", "c2"]


def test_layout_clean_single_file_with_o_writes_to_file(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_file = _write(tmp_path / "ok.gitsvg.jsonl", _OK_JSONL)
    output_file = tmp_path / "out.layout.json"
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["layout", str(input_file), "-o", str(output_file)])

    # --- assert -----------------------
    assert result.exit_code == 0
    payload = json.loads(output_file.read_text())
    assert payload["grid"] == {"n_commits": 2, "n_branches": 1}


def test_layout_invalid_file_writes_errors_to_stderr_and_no_json(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_file = _write(tmp_path / "bad.gitsvg.jsonl", _BAD_JSONL)
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["layout", str(input_file)])

    # --- assert -----------------------
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "[E" in result.stderr


def test_layout_invalid_file_with_o_writes_nothing(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_file = _write(tmp_path / "bad.gitsvg.jsonl", _BAD_JSONL)
    output_file = tmp_path / "out.layout.json"
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["layout", str(input_file), "-o", str(output_file)])

    # --- assert -----------------------
    assert result.exit_code == 1
    assert not output_file.exists()


def test_layout_dir_input_without_output_errors(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["layout", str(input_dir)])

    # --- assert -----------------------
    assert result.exit_code == 2
    assert "directory" in result.stderr
    assert "-o" in result.stderr


def test_layout_dir_pair_walks_inputs_and_writes_layout_jsons(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_root = tmp_path / "in"
    output_root = tmp_path / "out"
    _write(input_root / "a.gitsvg.jsonl", _OK_JSONL)
    _write(input_root / "sub" / "b.gitsvg.jsonl", _OK_JSONL)
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["layout", str(input_root), "-o", str(output_root)])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert (output_root / "a.layout.json").exists()
    assert (output_root / "sub" / "b.layout.json").exists()


def test_layout_dir_pair_aggregates_failures_and_exits_one(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_root = tmp_path / "in"
    output_root = tmp_path / "out"
    _write(input_root / "good.gitsvg.jsonl", _OK_JSONL)
    _write(input_root / "bad.gitsvg.jsonl", _BAD_JSONL)
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["layout", str(input_root), "-o", str(output_root)])

    # --- assert -----------------------
    assert result.exit_code == 1
    assert (output_root / "good.layout.json").exists()
    assert not (output_root / "bad.layout.json").exists()
    assert "1/2 files processed cleanly" in result.stderr


def test_layout_file_input_with_existing_dir_output_errors(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_file = _write(tmp_path / "x.gitsvg.jsonl", _OK_JSONL)
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["layout", str(input_file), "-o", str(output_dir)])

    # --- assert -----------------------
    assert result.exit_code == 2
    assert "OUTPUT exists as a directory" in result.stderr
