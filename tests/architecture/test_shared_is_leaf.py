"""Architecture meta-test: `gitsvg/_shared/` is a dependency-free leaf.

`gitsvg/_shared/` holds the cross-cutting primitives (the presentational
value-types, and small stage-agnostic helpers) that every pipeline stage
imports one-way. To stay a true leaf — and to keep the `file_format` ↔
`theme` import cycle it dissolved from ever returning — it must import
nothing from the rest of `gitsvg`; only intra-`_shared` imports are
allowed.

This test AST-scans every module under `gitsvg/_shared/` and asserts no
import targets a `gitsvg.*` module outside `gitsvg._shared`. It hardcodes
no symbol or module list, so there is nothing to keep in sync — the only
thing that makes it fail is an actual new dependency edge out of the leaf.
"""

import ast
from pathlib import Path

import gitsvg

_SHARED_PREFIX = "gitsvg._shared"


def _shared_modules() -> list[Path]:
    """Return every `.py` file under `gitsvg/_shared/`."""
    shared_root = Path(gitsvg.__file__).parent / "_shared"
    return sorted(shared_root.rglob("*.py"))


def _external_gitsvg_imports(path: Path) -> list[str]:
    """Return imported `gitsvg.*` module names that live outside `gitsvg._shared`.

    Relative imports (`from . import x`) are intra-`_shared` by
    construction and never flagged; only absolute `gitsvg.*` targets
    outside the leaf count.
    """
    tree = ast.parse(path.read_text())
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_external_gitsvg(alias.name):
                    offenders.append(alias.name)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module is not None
            and _is_external_gitsvg(node.module)
        ):
            offenders.append(node.module)
    return offenders


def _is_external_gitsvg(module: str) -> bool:
    """True for a `gitsvg` module that is not part of `gitsvg._shared`."""
    return (module == "gitsvg" or module.startswith("gitsvg.")) and not module.startswith(_SHARED_PREFIX)


def test_shared_is_dependency_free_leaf() -> None:
    """No module under `gitsvg/_shared/` may import from `gitsvg` outside `_shared`."""
    package_root = Path(gitsvg.__file__).parent.parent

    violations: list[str] = []
    for module_path in _shared_modules():
        for imported in _external_gitsvg_imports(module_path):
            violations.append(f"{module_path.relative_to(package_root)} -> {imported}")
    assert not violations, (
        f"gitsvg/_shared/ must be a dependency-free leaf; external gitsvg imports found: {violations}"
    )
