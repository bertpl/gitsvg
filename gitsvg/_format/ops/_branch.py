"""The `branch` operation."""

from typing import Literal

from gitsvg._format.ops._base import OpBase


class BranchOp(OpBase):
    """Declare a branch (optionally rooted on another branch's tip or a commit)."""

    op: Literal["branch"]
    name: str
    from_branch: str | None = None
    from_commit: str | None = None
    color: str | None = None
    label_side: Literal["left", "right"] | None = None
    branch_pos: int | None = None
