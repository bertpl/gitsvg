"""Architecture meta-tests: the pipeline-split boundary.

`Theme` lives only at the orchestration layer between the apply pass
and the layout / renderer stages. The two stage-side slices
(`LayoutSettings`, `RendererSettings`) flow downstream; the
orchestration class (`Theme`) does not. These tests parse the imports
of every module under `gitsvg/layout/` and `gitsvg/render/` and assert
that none of them import the `Theme` name directly — re-introducing
a `Theme` import silently re-couples the stage to the orchestration
class.

Exempted: `gitsvg/render/_renderer_settings.py` defines
`RendererSettings` as a `Theme` subclass and necessarily imports the
parent class.
"""

import ast
from pathlib import Path

import pytest

import gitsvg

# Files allowed to import `Theme` despite living under a stage package.
# `_renderer_settings.py` defines `RendererSettings` as a `Theme` subclass
# (the bridge between the orchestration class and the renderer slice).
_EXEMPT_FILES: frozenset[Path] = frozenset(
    {
        Path(gitsvg.__file__).parent / "render" / "_renderer_settings.py",
    }
)


def _stage_modules(stage_subdir: str) -> list[Path]:
    """Return every `.py` file under `gitsvg/<stage_subdir>/`."""
    stage_root = Path(gitsvg.__file__).parent / stage_subdir
    return sorted(stage_root.rglob("*.py"))


def _imports_theme(path: Path) -> bool:
    """Return True when `path`'s import statements reference `Theme` by name.

    Catches:
    - `from gitsvg.theme import Theme` (and variants with other names alongside)
    - `from gitsvg.theme._theme import Theme`
    - `import gitsvg.theme.Theme as ...` (any aliasing)

    Does NOT flag docstring / comment / string occurrences of "Theme" —
    only AST import nodes.
    """
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "Theme":
                    return True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                # Catches `import gitsvg.theme.Theme` (would actually be a
                # `from ... import Theme`, but check defensively).
                if alias.name.endswith(".Theme"):
                    return True
    return False


@pytest.mark.parametrize("stage", ["layout", "render"])
def test_stage_modules_do_not_import_theme(stage: str) -> None:
    """`gitsvg/<stage>/` must not import the `Theme` class.

    The pipeline split keeps `Theme` at the orchestration layer;
    stages consume `LayoutSettings` / `RendererSettings` slices via
    `Theme.split()`. The architecture meta-test guards against
    re-coupling a stage to `Theme` directly.
    """
    # --- arrange ----------------------
    modules = _stage_modules(stage)

    # --- act / assert -----------------
    violations: list[str] = []
    for module_path in modules:
        if module_path in _EXEMPT_FILES:
            continue
        if _imports_theme(module_path):
            violations.append(str(module_path.relative_to(Path(gitsvg.__file__).parent.parent)))
    assert not violations, (
        f"{stage}/ modules must consume the {stage} slice via Theme.split(); "
        f"the following modules still import Theme: {violations}"
    )
