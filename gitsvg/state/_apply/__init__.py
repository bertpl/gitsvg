"""Per-op apply handlers for state-mutating ops.

Subpackage layout:

- `_impl/` — one module per state-mutating op type, exposing
  `apply_<op>_op(state, theme, parsed, report) -> None`.
- `_checks/` — cross-cutting semantic checks an op handler invokes
  when its field set needs a multi-rule sweep beyond pydantic.

The `theme:` op handler lives outside this package, under
`gitsvg.theme._apply` — theme ops mutate `Theme`, not `State`. The
state engine routes by op type, calling the right home with the
shared `(state, theme, parsed, report)` signature.

External callers should import the handlers from this package directly.
"""

from gitsvg.state._apply._impl import (
    apply_branch_op,
    apply_commit_op,
    apply_grid_op,
    apply_highlight_op,
    apply_merge_op,
    apply_pull_request_op,
    apply_remove_op,
)

__all__ = [
    "apply_branch_op",
    "apply_commit_op",
    "apply_grid_op",
    "apply_highlight_op",
    "apply_merge_op",
    "apply_pull_request_op",
    "apply_remove_op",
]
