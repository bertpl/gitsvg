"""The `commit` operation."""

from typing import Literal, Self

from pydantic import Field, model_validator

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import IdStr, NonEmptyStr, NonNegativeInt


class CommitOp(OpBase):
    """Append a commit to a branch.

    `hash:` accepts the literal sentinel `"auto"`; deterministic
    resolution is implemented in v0.0.3.
    """

    op: Literal["commit"]
    branch: IdStr
    id: IdStr | None = None
    msg: NonEmptyStr | None = None
    hash: IdStr | None = None
    parents: list[IdStr] | None = Field(default=None, min_length=1)
    replaces: list[IdStr] | None = Field(default=None, min_length=1)
    highlight: bool | None = None
    commit_pos: NonNegativeInt | None = None
    branch_pos: NonNegativeInt | None = None

    @model_validator(mode="after")
    def _validate_msg_or_hash_present(self) -> Self:
        """Require at least one of `msg` or `hash` to be set."""
        if self.msg is None and self.hash is None:
            raise ValueError("commit op must specify at least one of 'msg' or 'hash'")
        return self
