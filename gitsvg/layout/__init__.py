"""Layout — assign axis positions to validated branches and commits.

Public surface:

- `compute_layout(parsed_ops)` — walk a stream of parsed ops in source
  order and return the resulting `Layout`.
- `Layout`, `LayoutBranch`, `LayoutCommit` — output dataclasses
  consumed by the renderer.

Layout is computed independently of the state engine: both walk the
same op stream, but state stores entity data (color, msg, hash,
parents, …) while layout stores axis positions. This keeps the
renderer free to read positions without depending on state-engine
internals, and keeps the layout engine swappable when smarter
heuristics land.
"""

from gitsvg.layout._engine import compute_layout
from gitsvg.layout._layout import Layout, LayoutBranch, LayoutCommit

__all__ = [
    "Layout",
    "LayoutBranch",
    "LayoutCommit",
    "compute_layout",
]
