"""Layout — turn validated `State` into a render-ready `Layout`.

Public surface:

- `compute_layout(state)` — pure transformation; takes the state engine's
  output and returns a complete `Layout` (integer-grid slot positions,
  resolved label sides, pre-computed arcs and guides, grid extent).
- `Layout`, `LayoutBranch`, `LayoutCommit`, `LayoutArc`, `LayoutGuide`,
  `LayoutPullRequest`, `LayoutGrid` — the dataclasses the renderer
  consumes.

Layout output is exclusively about integer-grid positioning. Colours,
fonts, pixel dimensions, and every other presentational decision live
on the resolved `Theme` the renderer reads.
"""

from gitsvg.layout._engine import compute_layout
from gitsvg.layout._layout import (
    Layout,
    LayoutArc,
    LayoutBranch,
    LayoutCommit,
    LayoutGrid,
    LayoutGuide,
    LayoutPullRequest,
)

__all__ = [
    "Layout",
    "LayoutArc",
    "LayoutBranch",
    "LayoutCommit",
    "LayoutGrid",
    "LayoutGuide",
    "LayoutPullRequest",
    "compute_layout",
]
