"""The `commit` operation."""

from typing import Literal

from gitsvg._file_format.ops._framework._base import OpBase


class CommitOp(OpBase):
    """Append a commit to a branch.

    `hash:` accepts the literal sentinel `"auto"`; deterministic
    resolution is implemented in v0.0.3.
    """

    op: Literal["commit"]
    branch: str
    id: str | None = None
    msg: str | None = None
    hash: str | None = None
    parents: list[str] | None = None
    replaces: list[str] | None = None
    highlight: bool | None = None
    commit_pos: int | None = None
    branch_pos: int | None = None
