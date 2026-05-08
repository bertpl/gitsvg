"""Apply a `highlight` op to state — flip the highlight flag on a commit."""

from typing import cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.file_format.ops import HighlightOp
from gitsvg.parse import ParsedOp
from gitsvg.state._state import State


def apply_highlight_op(state: State, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `highlight` op — set `highlight=True` on the targeted commit.

    The targeted commit must exist (E201). Highlighting an already-
    highlighted commit is a no-op (idempotent).
    """
    op = cast(HighlightOp, parsed.op)
    if not state.has_commit(op.commit):
        report.add(
            ValidationError(
                file=parsed.file,
                line=parsed.line,
                code="E201",
                message=f"commit {op.commit!r} is not declared",
                field="commit",
            )
        )
        return
    state.commits[op.commit].highlight = True
