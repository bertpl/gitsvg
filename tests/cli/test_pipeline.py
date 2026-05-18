"""Tests for the shared validate-pipeline helper."""

from pathlib import Path

from gitsvg.cli._pipeline import run_validate_pipeline


def _write(path: Path, content: str) -> Path:
    """Write `content` to `path` and return the path."""
    path.write_text(content, encoding="utf-8")
    return path


def test_run_validate_pipeline_clean_input_returns_state_clean_report_theme(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = _write(
        tmp_path / "ok.gitsvg.jsonl",
        '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "msg": "x"}\n',
    )

    # --- act --------------------------
    state, report, theme = run_validate_pipeline(file)

    # --- assert -----------------------
    assert report.is_clean()
    assert state is not None
    assert theme is not None


def test_run_validate_pipeline_dirty_input_returns_errors(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = _write(
        tmp_path / "bad.gitsvg.jsonl",
        '{"op": "commit", "branch": "main", "msg": "x"}\n',  # main not declared
    )

    # --- act --------------------------
    _state, report, _theme = run_validate_pipeline(file)

    # --- assert -----------------------
    assert not report.is_clean()
    assert len(report.errors) > 0


def test_run_validate_pipeline_resolves_imports(tmp_path: Path) -> None:
    # --- arrange ----------------------
    base = _write(
        tmp_path / "base.gitsvg.jsonl",
        '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n',
    )
    derived = _write(
        tmp_path / "derived.gitsvg.jsonl",
        f'{{"op": "import", "path": "./{base.name}"}}\n{{"op": "highlight", "commit": "c1"}}\n',
    )

    # --- act --------------------------
    _state, report, _theme = run_validate_pipeline(derived)

    # --- assert -----------------------
    assert report.is_clean()


def test_run_validate_pipeline_runs_end_of_file_checks(tmp_path: Path) -> None:
    # --- arrange ----------------------
    file = _write(
        tmp_path / "dangling.gitsvg.jsonl",
        (
            '{"op": "branch", "name": "main"}\n'
            '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
            '{"op": "branch", "name": "feat", "from_commit": "c1"}\n'
            '{"op": "remove", "commits": ["c1"]}\n'
        ),
    )

    # --- act --------------------------
    _state, report, _theme = run_validate_pipeline(file)

    # --- assert -----------------------
    assert not report.is_clean()
    assert any(e.code == "E400" for e in report.errors)
