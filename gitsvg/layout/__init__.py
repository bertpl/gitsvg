"""Layout — turn validated `State` into a render-ready `Layout`.

Public surface:

- `compute_layout(state)` — pure transformation; takes the state engine's
  output and returns a complete `Layout` (integer-grid slot positions,
  resolved label sides, pre-computed arcs, grid extent).
- `Layout`, `LayoutBranch`, `LayoutCommit`, `LayoutArc`, `LayoutArcKind`,
  `LayoutPullRequest`, `LayoutGrid` — the dataclasses (and arc-kind
  enum) the renderer consumes.

Layout output is exclusively about integer-grid positioning. Colours,
fonts, pixel dimensions, and every other presentational decision live
on the resolved `Theme` the renderer reads.
"""

from gitsvg.layout._engine import compute_layout
from gitsvg.layout._layout import (
    Layout,
    LayoutArc,
    LayoutArcKind,
    LayoutBranch,
    LayoutCommit,
    LayoutGrid,
    LayoutPullRequest,
)
from gitsvg.layout._serialisation import layout_to_json

__all__ = [
    "Layout",
    "LayoutArc",
    "LayoutArcKind",
    "LayoutBranch",
    "LayoutCommit",
    "LayoutGrid",
    "LayoutPullRequest",
    "compute_layout",
    "layout_to_json",
]
