"""Architecture meta-test: the layout/state orientation-blind boundary.

Invariant 7 (`docs/architecture.md`): the geometry-producing stages —
`gitsvg/layout/` and `gitsvg/state/` — are orientation-blind. They emit
canonical grid positions and side hints with no notion of screen
direction; the renderer (and the validate stage, for feature-support
gates like E223) is where `theme.orientation` is consulted.

This test parses every module under those two packages and asserts none
references the `Orientation` enum or accesses an `.orientation`
attribute — the executable form of the invariant, with no exemptions.
Docstring / comment mentions of "orientation" are not flagged; only AST
attribute and name nodes are.
"""

import ast
from pathlib import Path

import pytest

import gitsvg


def _stage_modules(stage_subdir: str) -> list[Path]:
    """Return every `.py` file under `gitsvg/<stage_subdir>/`."""
    stage_root = Path(gitsvg.__file__).parent / stage_subdir
    return sorted(stage_root.rglob("*.py"))


def _orientation_uses(path: Path) -> list[int]:
    """Return the line numbers where `path` references orientation in code.

    Catches both `<expr>.orientation` attribute access and any reference
    to the `Orientation` enum by name (import, comparison, annotation).
    Prose occurrences of "orientation" in docstrings or comments are not
    flagged — only AST attribute and name nodes.
    """
    tree = ast.parse(path.read_text())
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "orientation":
            lines.append(node.lineno)
        elif isinstance(node, ast.Name) and node.id == "Orientation":
            lines.append(node.lineno)
    return sorted(lines)


@pytest.mark.parametrize("stage", ["layout", "state"])
def test_stage_is_orientation_blind(stage: str) -> None:
    """`gitsvg/<stage>/` must not consult orientation.

    Orientation is a renderer-only (and validate-only feature-gate)
    concern; the layout and state stages emit canonical, direction-free
    geometry. A reference here re-introduces the leak invariant 7 forbids.
    """
    # --- arrange ----------------------
    package_root = Path(gitsvg.__file__).parent.parent

    # --- act / assert -----------------
    violations: list[str] = []
    for module_path in _stage_modules(stage):
        for line in _orientation_uses(module_path):
            violations.append(f"{module_path.relative_to(package_root)}:{line}")
    assert not violations, (
        f"{stage}/ must stay orientation-blind (invariant 7); orientation references found at: {violations}"
    )
