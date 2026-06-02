"""The `commit` operation."""

from typing import Literal, Self

from pydantic import Field, model_validator

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import IdStr, NonEmptyStr, NonNegativeInt


class CommitOp(OpBase):
    """Append a commit to a branch.

    `hash:` accepts the literal sentinel `"auto"`; auto-resolution is
    deterministic.
    """

    op: Literal["commit"]
    branch: IdStr = Field(description="Branch the commit lives on.")
    id: IdStr | None = Field(
        default=None,
        description="Explicit commit id; auto-generated when omitted.",
    )
    msg: NonEmptyStr | None = Field(
        default=None,
        description="Commit message; at least one of `msg` or `hash` must be set.",
    )
    hash: IdStr | None = Field(
        default=None,
        description=(
            'Commit hash string; the literal sentinel `"auto"` resolves to a deterministic 7-character hex '
            "derived from the commit's id and parent ids."
        ),
    )
    replaces: list[IdStr] | None = Field(
        default=None,
        min_length=1,
        description="Commit ids this commit conceptually squashes; the squashed commits are removed from state.",
    )
    highlight: bool | None = Field(
        default=None,
        description="When True, the commit renders with a highlight (enlarged dot + bold label).",
    )
    gap: NonNegativeInt | None = Field(
        default=None,
        description="Number of empty commit-axis slots between the branch's tip and this commit's landing position.",
    )

    @model_validator(mode="after")
    def _validate_msg_or_hash_present(self) -> Self:
        """Require at least one of `msg` or `hash` to be set."""
        if self.msg is None and self.hash is None:
            raise ValueError("commit op must specify at least one of 'msg' or 'hash'")
        return self
