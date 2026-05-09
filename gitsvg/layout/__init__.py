"""Layout — turn validated `State` into a render-ready `Layout`.

Public surface:

- `compute_layout(state)` — pure transformation; takes the state engine's
  output and returns a complete `Layout` (positions, resolved colours,
  resolved label sides, pre-computed arcs and guides, canvas dimensions).
- `Layout`, `LayoutBranch`, `LayoutCommit`, `LayoutArc`, `LayoutGuide`,
  `LayoutCanvas` — the dataclasses the renderer consumes.

The renderer never imports `State`. Every field it needs is pre-resolved
in `Layout`, so different layout strategies (the v0.0.3 default;
v0.0.4 lane reuse; future left-to-right orientation; …) can be plugged
in without touching the renderer.
"""

from gitsvg.layout._engine import compute_layout
from gitsvg.layout._layout import (
    Layout,
    LayoutArc,
    LayoutBranch,
    LayoutCanvas,
    LayoutCommit,
    LayoutGuide,
)

__all__ = [
    "Layout",
    "LayoutArc",
    "LayoutBranch",
    "LayoutCanvas",
    "LayoutCommit",
    "LayoutGuide",
    "compute_layout",
]
