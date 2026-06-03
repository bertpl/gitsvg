"""Per-op apply handlers, re-exported for the state engine.

Subpackage layout:

- `_impl/` — one module per op type, exposing
  `apply_<op>_op(state, builder, parsed, report) -> None`.
- `_checks/` — cross-cutting semantic checks an op handler invokes
  when its field set needs a multi-rule sweep beyond pydantic.

Every op handler — including the `theme:` handler, which mutates only
the `ThemeBuilder` and leaves `State` untouched — shares the uniform
`(state, builder, parsed, report)` signature; the engine routes by op
type. External callers import the handlers from this package directly.
"""

from ._impl import (
    apply_branch_op,
    apply_commit_op,
    apply_grid_op,
    apply_highlight_op,
    apply_merge_op,
    apply_pull_request_op,
    apply_remove_op,
    apply_theme_op,
)

__all__ = [
    "apply_branch_op",
    "apply_commit_op",
    "apply_grid_op",
    "apply_highlight_op",
    "apply_merge_op",
    "apply_pull_request_op",
    "apply_remove_op",
    "apply_theme_op",
]
