"""CLI tests for `gitsvg render`."""

from pathlib import Path

from click.testing import CliRunner

from gitsvg.cli._cli import cli


def _write(path: Path, content: str) -> Path:
    """Write `content` to `path` and return the path."""
    path.write_text(content, encoding="utf-8")
    return path


def test_render_clean_file_writes_svg_and_exits_zero(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_file = _write(
        tmp_path / "ok.gitsvg.jsonl",
        '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "msg": "x"}\n',
    )
    output_file = tmp_path / "out.svg"
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["render", str(input_file), "-o", str(output_file)])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert output_file.exists()
    text = output_file.read_text(encoding="utf-8")
    assert "<svg" in text
    assert "<circle" in text  # one commit dot


def test_render_invalid_file_exits_non_zero_and_writes_no_output(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_file = _write(
        tmp_path / "bad.gitsvg.jsonl",
        '{"op": "commit", "branch": "main", "msg": "x"}\n',  # main not declared
    )
    output_file = tmp_path / "out.svg"
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["render", str(input_file), "-o", str(output_file)])

    # --- assert -----------------------
    assert result.exit_code != 0
    assert not output_file.exists()


def test_render_requires_output_flag(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_file = _write(
        tmp_path / "ok.gitsvg.jsonl",
        '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "msg": "x"}\n',
    )
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["render", str(input_file)])

    # --- assert -----------------------
    assert result.exit_code != 0
    assert "missing option" in result.output.lower() or "-o" in result.output.lower()
