"""Snapshot tests for `gitsvg layout` over the shipped `examples/` folder.

For every `examples/<name>.gitsvg.jsonl`, generates the layout JSON
and asserts it byte-equal to the committed snapshot at
`tests/examples/_layout_snapshots/<name>.layout.json`. Guards against
silent drift in the layout→JSON serialisation surface.

To regenerate after an intentional change:

    uv run gitsvg layout examples -o tests/examples/_layout_snapshots
"""

import json
from pathlib import Path

import pytest

from gitsvg.cli._pipeline import run_validate_pipeline
from gitsvg.layout import compute_layout, layout_to_json

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
SNAPSHOTS_DIR = Path(__file__).parent / "_layout_snapshots"


def _example_files() -> list[Path]:
    """Return all `*.gitsvg.jsonl` files in `examples/`, sorted."""
    return sorted(EXAMPLES_DIR.glob("*.gitsvg.jsonl"))


EXAMPLE_FILES = _example_files()


@pytest.mark.parametrize("path", EXAMPLE_FILES, ids=lambda p: p.name)
def test_example_layout_matches_snapshot(path: Path) -> None:
    """Each example's layout JSON must byte-match its committed snapshot."""
    # --- arrange ----------------------
    stem = path.name.removesuffix(".gitsvg.jsonl")
    snapshot_path = SNAPSHOTS_DIR / f"{stem}.layout.json"
    assert snapshot_path.exists(), (
        f"missing snapshot {snapshot_path} — regenerate with "
        f"`uv run gitsvg layout examples -o tests/examples/_layout_snapshots`"
    )

    # --- act --------------------------
    state, report, theme = run_validate_pipeline(path)
    assert report.is_clean(), f"{path.name}: unexpected validation errors"
    layout_settings, _ = theme.split()
    produced = json.dumps(layout_to_json(compute_layout(state, layout_settings)), indent=2) + "\n"

    # --- assert -----------------------
    expected = snapshot_path.read_text()
    assert produced == expected, (
        f"{path.name}: layout JSON has drifted from snapshot. "
        f"Inspect the diff, then regenerate via "
        f"`uv run gitsvg layout examples -o tests/examples/_layout_snapshots` "
        f"when the change is intentional."
    )
