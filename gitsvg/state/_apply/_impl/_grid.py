"""Apply a `grid` op to state — pin the integer-grid extent for downstream layout."""

from typing import cast

from gitsvg.errors import ValidationReport
from gitsvg.file_format.ops import GridOp
from gitsvg.parse import ParsedOp
from gitsvg.state._state import GridState, State
from gitsvg.theme import ThemeBuilder


def apply_grid_op(state: State, builder: ThemeBuilder, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `grid` op — overwrite any prior grid pin.

    Passive at this layer — no semantic checks beyond the schema phase
    that already ran. Successive `grid` ops overwrite each other; the
    last one wins.
    """
    _ = report  # grid op never emits semantic errors
    op = cast(GridOp, parsed.op)
    state.grid = GridState(
        n_commits=op.n_commits,
        n_branches=op.n_branches,
    )
