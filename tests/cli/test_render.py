"""CLI tests for `gitsvg render`."""

from pathlib import Path

from click.testing import CliRunner

from gitsvg.cli._cli import cli
from tests._jsonl import build_jsonl

_OK_JSONL = build_jsonl({"op": "branch", "name": "main"}, {"op": "commit", "branch": "main", "msg": "x"})
_BAD_JSONL = build_jsonl({"op": "commit", "branch": "main", "msg": "x"})  # main not declared


def _write(path: Path, content: str) -> Path:
    """Write `content` to `path` (creating parents) and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_render_clean_file_writes_svg_and_exits_zero(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_file = _write(
        tmp_path / "ok.gitsvg.jsonl",
        build_jsonl({"op": "branch", "name": "main"}, {"op": "commit", "branch": "main", "msg": "x"}),
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
        build_jsonl({"op": "commit", "branch": "main", "msg": "x"}),  # main not declared
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
        build_jsonl({"op": "branch", "name": "main"}, {"op": "commit", "branch": "main", "msg": "x"}),
    )
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["render", str(input_file)])

    # --- assert -----------------------
    assert result.exit_code != 0
    assert "missing option" in result.output.lower() or "-o" in result.output.lower()


# ==================================================================================================
#  Directory-pair (bulk) invocation form
# ==================================================================================================
def test_render_dir_pair_walks_inputs_and_writes_mirrored_svgs(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_root = tmp_path / "in"
    output_root = tmp_path / "out"
    _write(input_root / "a.gitsvg.jsonl", _OK_JSONL)
    _write(input_root / "sub" / "b.gitsvg.jsonl", _OK_JSONL)
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["render", str(input_root), "-o", str(output_root)])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert (output_root / "a.svg").exists()
    assert (output_root / "sub" / "b.svg").exists()


def test_render_dir_pair_aggregates_failures_and_exits_one(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_root = tmp_path / "in"
    output_root = tmp_path / "out"
    _write(input_root / "good.gitsvg.jsonl", _OK_JSONL)
    _write(input_root / "bad.gitsvg.jsonl", _BAD_JSONL)
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["render", str(input_root), "-o", str(output_root)])

    # --- assert -----------------------
    assert result.exit_code == 1
    assert (output_root / "good.svg").exists()
    assert not (output_root / "bad.svg").exists()
    assert "1/2 files processed cleanly" in result.stderr
    assert "bad.gitsvg.jsonl" in result.stderr


def test_render_dir_pair_empty_input_dir_exits_zero_with_notice(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_root = tmp_path / "in"
    input_root.mkdir()
    output_root = tmp_path / "out"
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["render", str(input_root), "-o", str(output_root)])

    # --- assert -----------------------
    assert result.exit_code == 0
    assert "no *.gitsvg.jsonl files found" in result.stderr


def test_render_file_input_with_existing_dir_output_errors(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_file = _write(tmp_path / "x.gitsvg.jsonl", _OK_JSONL)
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["render", str(input_file), "-o", str(output_dir)])

    # --- assert -----------------------
    assert result.exit_code == 2
    assert "OUTPUT exists as a directory" in result.stderr


def test_render_dir_input_with_existing_file_output_errors(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    output_file = _write(tmp_path / "out.svg", "")
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(cli, ["render", str(input_dir), "-o", str(output_file)])

    # --- assert -----------------------
    assert result.exit_code == 2
    assert "OUTPUT exists as a file" in result.stderr
