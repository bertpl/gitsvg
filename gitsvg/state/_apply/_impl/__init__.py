"""Per-op apply handlers — one module per op type.

Each module exposes a single `apply_<op>_op(state, parsed, report) -> None`
that mutates state in place when the op applies cleanly and appends
semantic errors to the report otherwise.
"""

from gitsvg.state._apply._impl._branch import apply_branch_op
from gitsvg.state._apply._impl._commit import apply_commit_op
from gitsvg.state._apply._impl._grid import apply_grid_op
from gitsvg.state._apply._impl._highlight import apply_highlight_op
from gitsvg.state._apply._impl._merge import apply_merge_op
from gitsvg.state._apply._impl._pull_request import apply_pull_request_op
from gitsvg.state._apply._impl._remove import apply_remove_op
from gitsvg.state._apply._impl._theme import apply_theme_op

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
