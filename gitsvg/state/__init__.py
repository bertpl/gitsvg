"""State engine — apply parsed ops to an in-memory diagram state.

Public surface:

- `apply_ops(parsed_ops, report)` — apply parsed ops in order,
  returning the resulting `(State, Theme)` pair. Semantic errors
  accumulate into the supplied `ValidationReport` (parser errors
  typically already populate it).
- `State`, `BranchState`, `CommitState`, `GridState` — state classes
  exposed for downstream consumers (layout, rendering) and for tests.
"""

from gitsvg.state._engine import apply_ops
from gitsvg.state._serialization import state_to_json
from gitsvg.state._state import BranchState, CommitState, GridState, State

__all__ = [
    "BranchState",
    "CommitState",
    "GridState",
    "State",
    "apply_ops",
    "state_to_json",
]
