"""Tests for the bulk walker + type-matrix dispatch helpers."""

from collections.abc import Callable
from pathlib import Path

import pytest

from gitsvg.cli._bulk import (
    mirror_output_path,
    print_report_errors,
    process_input,
    run_bulk,
    walk_inputs,
)
from gitsvg.errors import ValidationError, ValidationReport


def _write(path: Path, content: str = "") -> Path:
    """Ensure `path`'s parents exist, write `content`, return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _clean_callback(out_text: str = "<svg/>") -> Callable[[Path, Path], ValidationReport]:
    """Return a process_one that writes `out_text` and reports clean."""

    def cb(input_path: Path, output_path: Path) -> ValidationReport:
        """Write the canned output text and return a clean report."""
        output_path.write_text(out_text)
        return ValidationReport()

    return cb


def _make_dirty_report(input_path: Path) -> ValidationReport:
    """Build a non-empty `ValidationReport` for tests needing a failing input."""
    report = ValidationReport()
    report.add(
        ValidationError(
            file=str(input_path),
            line=1,
            code="E101",
            message="synthetic test error",
            field=None,
            suggestion=None,
        )
    )
    return report


# ==================================================================================================
#  walk_inputs
# ==================================================================================================
def test_walk_inputs_returns_sorted_matches_across_subdirs(tmp_path: Path) -> None:
    # --- arrange ----------------------
    _write(tmp_path / "b" / "second.gitsvg.jsonl")
    _write(tmp_path / "a" / "first.gitsvg.jsonl")
    _write(tmp_path / "noise.txt")

    # --- act --------------------------
    found = walk_inputs(tmp_path)

    # --- assert -----------------------
    assert [p.relative_to(tmp_path) for p in found] == [
        Path("a/first.gitsvg.jsonl"),
        Path("b/second.gitsvg.jsonl"),
    ]


def test_walk_inputs_missing_dir_returns_empty(tmp_path: Path) -> None:
    # --- arrange / act ----------------
    found = walk_inputs(tmp_path / "does_not_exist")

    # --- assert -----------------------
    assert found == []


def test_walk_inputs_empty_dir_returns_empty(tmp_path: Path) -> None:
    # --- arrange / act ----------------
    found = walk_inputs(tmp_path)

    # --- assert -----------------------
    assert found == []


# ==================================================================================================
#  mirror_output_path
# ==================================================================================================
def test_mirror_output_path_preserves_subdir_structure(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_root = tmp_path / "in"
    output_root = tmp_path / "out"
    input_file = input_root / "story" / "frame.gitsvg.jsonl"

    # --- act --------------------------
    output = mirror_output_path(input_file, input_root, output_root, ".svg")

    # --- assert -----------------------
    assert output == output_root / "story" / "frame.svg"


def test_mirror_output_path_top_level_input_swaps_extension(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_root = tmp_path / "in"
    output_root = tmp_path / "out"
    input_file = input_root / "x.gitsvg.jsonl"

    # --- act --------------------------
    output = mirror_output_path(input_file, input_root, output_root, ".state.json")

    # --- assert -----------------------
    assert output == output_root / "x.state.json"


def test_mirror_output_path_rejects_non_gitsvg_suffix(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_root = tmp_path / "in"
    output_root = tmp_path / "out"
    input_file = input_root / "x.txt"

    # --- act / assert -----------------
    with pytest.raises(ValueError, match="gitsvg.jsonl"):
        mirror_output_path(input_file, input_root, output_root, ".svg")


# ==================================================================================================
#  run_bulk
# ==================================================================================================
def test_run_bulk_processes_each_input_under_mirrored_paths(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_root = tmp_path / "in"
    output_root = tmp_path / "out"
    _write(input_root / "a.gitsvg.jsonl")
    _write(input_root / "sub" / "b.gitsvg.jsonl")

    # --- act --------------------------
    code = run_bulk(input_root, output_root, ".svg", _clean_callback())

    # --- assert -----------------------
    assert code == 0
    assert (output_root / "a.svg").read_text() == "<svg/>"
    assert (output_root / "sub" / "b.svg").read_text() == "<svg/>"


def test_run_bulk_empty_input_dir_returns_zero_with_notice(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # --- arrange ----------------------
    input_root = tmp_path / "empty"
    input_root.mkdir()
    output_root = tmp_path / "out"

    # --- act --------------------------
    code = run_bulk(input_root, output_root, ".svg", _clean_callback())

    # --- assert -----------------------
    assert code == 0
    assert "no *.gitsvg.jsonl files found" in capsys.readouterr().err


def test_run_bulk_aggregates_failures_continues_walk_and_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # --- arrange ----------------------
    input_root = tmp_path / "in"
    output_root = tmp_path / "out"
    _write(input_root / "good.gitsvg.jsonl")
    _write(input_root / "bad.gitsvg.jsonl")

    def cb(input_path: Path, output_path: Path) -> ValidationReport:
        """Pass on `good.*`, fail on `bad.*`."""
        if input_path.name == "bad.gitsvg.jsonl":
            return _make_dirty_report(input_path)
        output_path.write_text("<svg/>")
        return ValidationReport()

    # --- act --------------------------
    code = run_bulk(input_root, output_root, ".svg", cb)

    # --- assert -----------------------
    assert code == 1
    assert (output_root / "good.svg").exists()
    assert not (output_root / "bad.svg").exists()
    err = capsys.readouterr().err
    assert "1/2 files processed cleanly" in err
    assert "bad.gitsvg.jsonl" in err
    assert "[E101]" in err


# ==================================================================================================
#  process_input — type-matrix dispatch
# ==================================================================================================
def test_process_input_file_to_file_calls_callback_once(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_file = _write(tmp_path / "x.gitsvg.jsonl")
    output_file = tmp_path / "x.svg"
    calls: list[tuple[Path, Path]] = []

    def cb(inp: Path, out: Path) -> ValidationReport:
        """Record the call and write a stub output."""
        calls.append((inp, out))
        out.write_text("<svg/>")
        return ValidationReport()

    # --- act --------------------------
    code = process_input(input_file, output_file, ".svg", cb)

    # --- assert -----------------------
    assert code == 0
    assert calls == [(input_file, output_file)]
    assert output_file.read_text() == "<svg/>"


def test_process_input_file_input_with_existing_dir_output_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # --- arrange ----------------------
    input_file = _write(tmp_path / "x.gitsvg.jsonl")
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    # --- act --------------------------
    code = process_input(input_file, output_dir, ".svg", _clean_callback())

    # --- assert -----------------------
    assert code == 2
    assert "OUTPUT exists as a directory" in capsys.readouterr().err


def test_process_input_dir_input_with_existing_file_output_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # --- arrange ----------------------
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    output_file = _write(tmp_path / "out.svg", "")

    # --- act --------------------------
    code = process_input(input_dir, output_file, ".svg", _clean_callback())

    # --- assert -----------------------
    assert code == 2
    assert "OUTPUT exists as a file" in capsys.readouterr().err


def test_process_input_dir_to_dir_dispatches_to_bulk(tmp_path: Path) -> None:
    # --- arrange ----------------------
    input_root = tmp_path / "in"
    output_root = tmp_path / "out"
    _write(input_root / "a.gitsvg.jsonl")
    _write(input_root / "b.gitsvg.jsonl")

    # --- act --------------------------
    code = process_input(input_root, output_root, ".svg", _clean_callback())

    # --- assert -----------------------
    assert code == 0
    assert (output_root / "a.svg").exists()
    assert (output_root / "b.svg").exists()


def test_process_input_single_file_failure_prints_errors_and_returns_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # --- arrange ----------------------
    input_file = _write(tmp_path / "x.gitsvg.jsonl")
    output_file = tmp_path / "x.svg"

    def cb(inp: Path, out: Path) -> ValidationReport:
        """Return a synthetic dirty report without writing output."""
        return _make_dirty_report(inp)

    # --- act --------------------------
    code = process_input(input_file, output_file, ".svg", cb)

    # --- assert -----------------------
    assert code == 1
    assert not output_file.exists()
    assert "[E101]" in capsys.readouterr().err


# ==================================================================================================
#  print_report_errors
# ==================================================================================================
def test_print_report_errors_writes_each_error_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    # --- arrange ----------------------
    report = ValidationReport()
    report.add(ValidationError(file="x.jsonl", line=1, code="E101", message="bad thing"))

    # --- act --------------------------
    print_report_errors(report)

    # --- assert -----------------------
    captured = capsys.readouterr()
    assert "x.jsonl:1: [E101] bad thing" in captured.err
    assert captured.out == ""


def test_print_report_errors_err_false_writes_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    # --- arrange ----------------------
    report = ValidationReport()
    report.add(ValidationError(file="x.jsonl", line=2, code="E101", message="oops"))

    # --- act --------------------------
    print_report_errors(report, err=False)

    # --- assert -----------------------
    captured = capsys.readouterr()
    assert "x.jsonl:2: [E101] oops" in captured.out
    assert captured.err == ""
