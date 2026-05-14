"""gitsvg — render git history diagrams from JSONL operations.

The package implements a five-stage validate-and-render pipeline:

    parse → imports → state → layout → render

Each stage lives in the matching subpackage; each stage's output is
the next stage's only input. The `state` stage emits two parallel
outputs — `State` (structural model) and `Theme` (resolved
presentational constants) — which `layout` and `render` consume
respectively. Cross-cutting subpackages sit alongside the pipeline:
`file_format/` (op schemas), `errors/` (error codes, catalog,
reports), `theme/` (the `Theme` dataclass + theme-op applier),
`cli/` (Click entry points).

See `docs/architecture.md` for the locked-in pipeline rule and the
companion invariants.
"""

from importlib.metadata import version

__version__ = version("gitsvg")
