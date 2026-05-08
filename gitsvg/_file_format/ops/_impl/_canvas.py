"""The `canvas` operation."""

from typing import Literal

from gitsvg._file_format.ops._framework._base import OpBase
from gitsvg._file_format.ops._framework._types import NonNegativeFloat, NonNegativeInt


class CanvasOp(OpBase):
    """Pin canvas dimensions; default (no `canvas` op) is auto-fit."""

    op: Literal["canvas"]
    n_commits: NonNegativeInt | None = None
    n_branches: NonNegativeInt | None = None
    commit_spacing: NonNegativeFloat | None = None
    branch_spacing: NonNegativeFloat | None = None
