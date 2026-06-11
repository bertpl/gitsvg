"""Architecture meta-tests: the pipeline-split boundary.

`Theme` lives only at the orchestration layer between the apply pass
and the layout / renderer stages. The two stage-side slices
(`LayoutSettings`, `RendererSettings`) flow downstream; the
orchestration class (`Theme`) does not. These tests parse the imports
of every module under `gitsvg/layout/` and `gitsvg/render/` and assert
that none of them import the `Theme` name directly — re-introducing
a `Theme` import silently re-couples the stage to the orchestration
class.

No exemptions: `RendererSettings` is a standalone schema mirroring
`Theme`'s field block with concrete types, so not even its defining
module imports `Theme`. A companion test asserts the two field sets
stay identical, so the mirrored block cannot drift.
"""

import ast
from pathlib import Path

import pytest

import gitsvg
from gitsvg.render._renderer_settings import RendererSettings
from gitsvg.theme import Theme


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
        if _imports_theme(module_path):
            violations.append(str(module_path.relative_to(Path(gitsvg.__file__).parent.parent)))
    assert not violations, (
        f"{stage}/ modules must consume the {stage} slice via Theme.split(); "
        f"the following modules still import Theme: {violations}"
    )


def test_renderer_settings_mirrors_theme_field_for_field() -> None:
    """`RendererSettings` re-declares `Theme`'s field block with concrete types.

    The duplication is deliberate (a static type checker cannot see
    through a dynamically derived model), so this guard is what keeps
    the two blocks from drifting: a field added to one must be added
    to the other.
    """
    # --- arrange ----------------------
    theme_fields = set(Theme.model_fields)
    renderer_fields = set(RendererSettings.model_fields)

    # --- assert -----------------------
    assert theme_fields == renderer_fields, (
        f"Theme/RendererSettings field drift — "
        f"only on Theme: {sorted(theme_fields - renderer_fields)}, "
        f"only on RendererSettings: {sorted(renderer_fields - theme_fields)}"
    )
