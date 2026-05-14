"""gitsvg — render git history diagrams from JSONL operations.

The package implements a five-stage validate-and-render pipeline:

    parse → imports → state → layout → render

Each stage lives in the matching subpackage; each stage's output is
the next stage's only input. Cross-cutting subpackages sit alongside
the pipeline: `file_format/` (op schemas), `errors/` (error codes,
catalog, reports), `cli/` (Click entry points), plus `_theme.py` at
the root (the `Theme` dataclass shared by `state/` and `render/`).

See `docs/architecture.md` for the locked-in pipeline rule and the
companion invariants.
"""

from importlib.metadata import version

__version__ = version("gitsvg")
