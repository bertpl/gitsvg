"""The `branch` operation."""

from typing import Literal, Self

from pydantic import model_validator

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import HexColor, IdStr


class BranchOp(OpBase):
    """Declare a branch (optionally rooted on another branch's tip or a commit)."""

    op: Literal["branch"]
    name: IdStr
    from_branch: IdStr | None = None
    from_commit: IdStr | None = None
    color: HexColor | None = None
    label_side: Literal["left", "right"] | None = None

    @model_validator(mode="after")
    def _validate_at_most_one_root(self) -> Self:
        """Reject specifying both `from_branch` and `from_commit`."""
        if self.from_branch is not None and self.from_commit is not None:
            raise ValueError("'from_branch' and 'from_commit' are mutually exclusive on a branch op")
        return self
