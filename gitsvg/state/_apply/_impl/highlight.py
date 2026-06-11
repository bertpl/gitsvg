"""Apply a `highlight` op to state — flip the highlight flag on a commit."""

from typing import TYPE_CHECKING, cast

from gitsvg.errors import ValidationReport
from gitsvg.parse import ParsedOp
from gitsvg.state._apply._errors import add_commit_not_declared
from gitsvg.state._state import State
from gitsvg.theme import ThemeBuilder

if TYPE_CHECKING:
    from gitsvg.file_format.ops import HighlightOp


def apply_highlight_op(state: State, builder: ThemeBuilder, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `highlight` op — set `highlight=True` on the targeted commit.

    The targeted commit must exist (E201). Highlighting an already-
    highlighted commit is a no-op (idempotent).
    """
    op = cast("HighlightOp", parsed.op)
    if not state.has_commit(op.commit):
        add_commit_not_declared(
            report, file=parsed.file, line=parsed.line, commit_id=op.commit, field="commit", declared=state.commits
        )
        return
    state.commits[op.commit].highlight = True
