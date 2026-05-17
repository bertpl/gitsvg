"""Unit tests for the `gitsvg render --small` CLI flag parsing.

Exercises the Click `flag_value` form: bare `--small` selects level 2,
`--small=N` selects level N, absent flag selects level 0.
"""

from pathlib import Path

import pytest
from click.testing import CliRunner

from gitsvg.cli._render import render_command

# A minimal valid input file fixture path. The actual render produces an SVG;
# we just need a clean validate so the command exits 0 and we can inspect side
# effects of the flag parsing.
_FIXTURE = "tests/render/test_minify/fixtures/cli_minimal.gitsvg.jsonl"


def _ensure_fixture() -> Path:
    """Write a minimal valid input fixture, returning its path."""
    path = Path(_FIXTURE)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            '{"op": "branch", "name": "main", "label_side": "before"}\n'
            '{"op": "commit", "branch": "main", "id": "c1", "msg": "one"}\n'
        )
    return path


@pytest.mark.parametrize(
    "flag_args, exit_code",
    [
        # Absent (no --small) → level 0; runs cleanly.
        ([], 0),
        # Bare --small → level 2.
        (["--small"], 0),
        # Explicit level values.
        (["--small=0"], 0),
        (["--small=1"], 0),
        (["--small=2"], 0),
        (["--small=3"], 0),
    ],
)
def test_small_flag_accepts_valid_invocations(tmp_path: Path, flag_args: list[str], exit_code: int) -> None:
    # --- arrange ----------------------
    fixture = _ensure_fixture()
    output = tmp_path / "out.svg"
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(render_command, [str(fixture), "-o", str(output), *flag_args])

    # --- assert -----------------------
    assert result.exit_code == exit_code, result.output
    assert output.exists()
    assert output.read_text().lstrip().startswith("<")


def test_small_flag_rejects_out_of_range_value(tmp_path: Path) -> None:
    # --- arrange ----------------------
    fixture = _ensure_fixture()
    output = tmp_path / "out.svg"
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(render_command, [str(fixture), "-o", str(output), "--small=4"])

    # --- assert -----------------------
    assert result.exit_code != 0
    assert "4" in result.output or "range" in result.output.lower()


def test_small_flag_rejects_non_integer_value(tmp_path: Path) -> None:
    # --- arrange ----------------------
    fixture = _ensure_fixture()
    output = tmp_path / "out.svg"
    runner = CliRunner()

    # --- act --------------------------
    result = runner.invoke(render_command, [str(fixture), "-o", str(output), "--small=foo"])

    # --- assert -----------------------
    assert result.exit_code != 0
