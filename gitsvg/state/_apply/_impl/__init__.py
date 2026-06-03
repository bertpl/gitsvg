"""Per-op apply handlers — one module per op type.

Each module exposes a single `apply_<op>_op` handler sharing the
uniform `(state, builder, parsed, report)` signature the engine
dispatches on. Most mutate `State` in place (the `branch:` / `remove:`
handlers also write per-branch overrides to the `ThemeBuilder`); the
`theme:` handler mutates only the `ThemeBuilder`, never `State`. Every
handler appends semantic errors to the report.
"""

from .branch import apply_branch_op
from .commit import apply_commit_op
from .grid import apply_grid_op
from .highlight import apply_highlight_op
from .merge import apply_merge_op
from .pull_request import apply_pull_request_op
from .remove import apply_remove_op
from .theme import apply_theme_op

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
