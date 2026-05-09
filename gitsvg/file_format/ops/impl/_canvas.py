"""The `canvas` operation."""

from typing import Literal

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import NonNegativeFloat, NonNegativeInt


class CanvasOp(OpBase):
    """Pin canvas dimensions; default (no `canvas` op) is auto-fit.

    Margin fields default to auto-fit (renderer reserves room based on
    the longest visible label on each side); set them explicitly only
    for animation series where stable per-frame margins matter.
    """

    op: Literal["canvas"]
    n_commits: NonNegativeInt | None = None
    n_branches: NonNegativeInt | None = None
    commit_spacing: NonNegativeFloat | None = None
    branch_spacing: NonNegativeFloat | None = None
    margin_commit_axis_lower: NonNegativeFloat | None = None
    margin_commit_axis_upper: NonNegativeFloat | None = None
    margin_branch_axis_lower: NonNegativeFloat | None = None
    margin_branch_axis_upper: NonNegativeFloat | None = None
