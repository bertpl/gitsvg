"""Snapshot tests for `gitsvg state` over the shipped `examples/` folder.

For every `examples/<name>.gitsvg.jsonl`, generates the state JSON
and asserts it byte-equal to the committed snapshot at
`tests/examples/_state_snapshots/<name>.state.json`. Guards against
silent drift in the state→JSON serialization surface.

To regenerate after an intentional change:

    uv run gitsvg state examples -o tests/examples/_state_snapshots
"""

import json
from pathlib import Path

import pytest

from gitsvg.cli._pipeline import run_validate_pipeline
from gitsvg.state import state_to_json

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
SNAPSHOTS_DIR = Path(__file__).parent / "_state_snapshots"


def _example_files() -> list[Path]:
    """Return all `*.gitsvg.jsonl` files in `examples/`, sorted."""
    return sorted(EXAMPLES_DIR.glob("*.gitsvg.jsonl"))


EXAMPLE_FILES = _example_files()


@pytest.mark.parametrize("path", EXAMPLE_FILES, ids=lambda p: p.name)
def test_example_state_matches_snapshot(path: Path) -> None:
    """Each example's state JSON must byte-match its committed snapshot."""
    # --- arrange ----------------------
    stem = path.name.removesuffix(".gitsvg.jsonl")
    snapshot_path = SNAPSHOTS_DIR / f"{stem}.state.json"
    assert snapshot_path.exists(), (
        f"missing snapshot {snapshot_path} — regenerate with "
        f"`uv run gitsvg state examples -o tests/examples/_state_snapshots`"
    )

    # --- act --------------------------
    state, report, _theme = run_validate_pipeline(path)
    assert report.is_clean(), f"{path.name}: unexpected validation errors"
    produced = json.dumps(state_to_json(state), indent=2) + "\n"

    # --- assert -----------------------
    expected = snapshot_path.read_text()
    assert produced == expected, (
        f"{path.name}: state JSON has drifted from snapshot. "
        f"Inspect the diff, then regenerate via "
        f"`uv run gitsvg state examples -o tests/examples/_state_snapshots` "
        f"when the change is intentional."
    )
