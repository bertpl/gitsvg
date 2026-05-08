"""State engine — apply parsed ops to an in-memory diagram state.

Public surface:

- `apply_ops(parsed_ops, report)` — apply parsed ops in order, returning
  the resulting `State`. Semantic errors accumulate into the supplied
  `ValidationReport` (parser errors typically already populate it).
- `State`, `BranchState`, `CommitState`, `CanvasState` — state classes
  exposed for downstream consumers (layout, rendering) and for tests.
"""

from gitsvg.state._engine import apply_ops
from gitsvg.state._state import BranchState, CanvasState, CommitState, State

__all__ = [
    "BranchState",
    "CanvasState",
    "CommitState",
    "State",
    "apply_ops",
]
