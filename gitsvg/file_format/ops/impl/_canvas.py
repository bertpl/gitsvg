"""The `canvas` operation."""

from typing import Literal

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import NonNegativeFloat, NonNegativeInt


class CanvasOp(OpBase):
    """Pin canvas dimensions; default (no `canvas` op) is auto-fit."""

    op: Literal["canvas"]
    n_commits: NonNegativeInt | None = None
    n_branches: NonNegativeInt | None = None
    commit_spacing: NonNegativeFloat | None = None
    branch_spacing: NonNegativeFloat | None = None
