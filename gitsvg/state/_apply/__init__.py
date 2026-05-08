"""Per-op apply handlers for the state engine.

One module per op type. Each module exposes a single `apply_<op>_op`
function with the signature `(state, parsed, report) -> None` — it
mutates state in place when the op applies cleanly, and appends
semantic errors to the report otherwise.
"""

from gitsvg.state._apply._branch import apply_branch_op
from gitsvg.state._apply._canvas import apply_canvas_op
from gitsvg.state._apply._commit import apply_commit_op
from gitsvg.state._apply._highlight import apply_highlight_op
from gitsvg.state._apply._merge import apply_merge_op
from gitsvg.state._apply._remove import apply_remove_op

__all__ = [
    "apply_branch_op",
    "apply_canvas_op",
    "apply_commit_op",
    "apply_highlight_op",
    "apply_merge_op",
    "apply_remove_op",
]
