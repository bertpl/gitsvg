"""Apply a `canvas` op to state — pin canvas dimensions for downstream layout."""

from typing import cast

from gitsvg.errors import ValidationReport
from gitsvg.file_format.ops import CanvasOp
from gitsvg.parse import ParsedOp
from gitsvg.state._state import CanvasState, State


def apply_canvas_op(state: State, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `canvas` op — overwrite any prior canvas spec.

    The canvas op is passive at this layer — no semantic checks beyond
    the shape phase that already ran. Successive `canvas` ops overwrite
    each other; the last one wins.
    """
    _ = report  # canvas op never emits semantic errors
    op = cast(CanvasOp, parsed.op)
    state.canvas = CanvasState(
        n_commits=op.n_commits,
        n_branches=op.n_branches,
        commit_spacing=op.commit_spacing,
        branch_spacing=op.branch_spacing,
    )
