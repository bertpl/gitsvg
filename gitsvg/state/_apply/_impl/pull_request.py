"""Apply a `pull_request` op to state — opens a pending merge between two branches."""

from typing import TYPE_CHECKING, cast

from gitsvg.errors import ValidationError, ValidationReport
from gitsvg.parse import ParsedOp
from gitsvg.state._apply._errors import add_branch_not_declared
from gitsvg.state._state import PullRequestState, State
from gitsvg.theme import ThemeBuilder

if TYPE_CHECKING:
    from gitsvg.file_format.ops import PullRequestOp


def apply_pull_request_op(state: State, builder: ThemeBuilder, parsed: ParsedOp, report: ValidationReport) -> None:
    """Apply a `pull_request` op.

    A pull-request is a third-namespace entity (alongside commits and
    branches) representing a pending merge. Both endpoints live-track
    the current tips of `from` and `into` at render time, so new
    commits on either side push the visual forward.

    Validation order:

    1. `from` and `into` must reference distinct branches (E210).
    2. `from` must reference an existing branch (E200).
    3. `into` must reference an existing branch (E200).
    4. The id (whether explicit or auto-generated) must not already
       be used by another open pull-request (E211).
    5. No open pull-request may already exist with the same
       `(from, into)` pair (E212).
    """
    op = cast("PullRequestOp", parsed.op)
    file = parsed.file
    line = parsed.line

    if op.from_ == op.into:
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E210",
                message=f"pull_request 'from' and 'into' must differ (both are {op.from_!r})",
                field="from",
            )
        )
        return

    if not state.has_branch(op.from_):
        add_branch_not_declared(report, file=file, line=line, branch=op.from_, field="from", declared=state.branches)
        return

    if not state.has_branch(op.into):
        add_branch_not_declared(report, file=file, line=line, branch=op.into, field="into", declared=state.branches)
        return

    pr_id = op.id if op.id is not None else _generate_auto_pr_id(state)
    if op.id is not None and op.id in state.pull_requests:
        report.add(
            ValidationError(
                file=file,
                line=line,
                code="E211",
                message=f"pull_request id {op.id!r} is already used",
                field="id",
            )
        )
        return

    for existing in state.pull_requests.values():
        if existing.from_branch == op.from_ and existing.into_branch == op.into:
            report.add(
                ValidationError(
                    file=file,
                    line=line,
                    code="E212",
                    message=(
                        f"a pull_request already exists from {op.from_!r} into {op.into!r} "
                        f"(id {existing.id!r}); close it via 'remove' before opening another"
                    ),
                )
            )
            return

    state.pull_requests[pr_id] = PullRequestState(
        id=pr_id,
        from_branch=op.from_,
        into_branch=op.into,
        title=op.title,
        declaration_file=file,
        declaration_line=line,
    )


# ==================================================================================================
#  Helpers
# ==================================================================================================
def _generate_auto_pr_id(state: State) -> str:
    """Return the lowest `_pr<N>` not already used by an open pull-request.

    The leading underscore is the convention for auto-generated ids;
    user-supplied ids should not start with `_`, which keeps the two
    namespaces from colliding.
    """
    n = 1
    while f"_pr{n}" in state.pull_requests:
        n += 1
    return f"_pr{n}"
