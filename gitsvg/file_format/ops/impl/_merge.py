"""The `merge` operation."""

from typing import Literal

from pydantic import Field

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import IdStr, NonEmptyStr, NonNegativeInt


class MergeOp(OpBase):
    """Two-parent commit on `into`, with an arc back to the tip of `from`.

    Blocked when an open pull-request matches the `(from, into)` pair
    — close the PR via `remove` first.
    """

    op: Literal["merge"]
    from_: IdStr = Field(
        alias="from",
        description="Branch whose tip becomes the second parent of the merge commit.",
    )
    into: IdStr = Field(
        description="Branch the merge commit is appended to (first parent is its prior tip).",
    )
    as_: IdStr | None = Field(
        default=None,
        alias="as",
        description="Explicit id for the merge commit; auto-generated when omitted.",
    )
    msg: NonEmptyStr | None = Field(
        default=None,
        description="Commit message for the merge commit.",
    )
    hash: IdStr | None = Field(
        default=None,
        description=(
            'Hash string for the merge commit; the literal sentinel `"auto"` resolves to a deterministic '
            "7-character hex derived from the commit's id and parent ids."
        ),
    )
    gap: NonNegativeInt | None = Field(
        default=None,
        description=(
            "Number of empty commit-axis slots above the natural anchor at `max(into.tip, from.tip) + 1` "
            "before the merge commit lands."
        ),
    )
