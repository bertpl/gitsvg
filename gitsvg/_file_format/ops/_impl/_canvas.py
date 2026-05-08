"""The `canvas` operation."""

from typing import Literal

from gitsvg._file_format.ops._framework._base import OpBase


class CanvasOp(OpBase):
    """Pin canvas dimensions; default (no `canvas` op) is auto-fit."""

    op: Literal["canvas"]
    n_commits: int | None = None
    n_branches: int | None = None
    commit_spacing: float | None = None
    branch_spacing: float | None = None
