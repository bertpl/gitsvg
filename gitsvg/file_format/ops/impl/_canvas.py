"""The `canvas` operation."""

from typing import Literal

from pydantic import Field

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import NonNegativeFloat, NonNegativeInt


class CanvasOp(OpBase):
    """Pin canvas dimensions; default (no `canvas` op) is auto-fit.

    Margin fields default to auto-fit (renderer reserves room based on
    the longest visible label on each side); set them explicitly only
    for animation series where stable per-frame margins matter.
    """

    op: Literal["canvas"]
    n_commits: NonNegativeInt | None = Field(
        default=None,
        description="Pinned commit-axis slot count; auto-fit from content when unset.",
    )
    n_branches: NonNegativeInt | None = Field(
        default=None,
        description="Pinned branch-axis slot count; auto-fit from content when unset.",
    )
    commit_spacing: NonNegativeFloat | None = Field(
        default=None,
        description="Pinned pixel distance between adjacent commit-axis slots; uses the renderer default when unset.",
    )
    branch_spacing: NonNegativeFloat | None = Field(
        default=None,
        description="Pinned pixel distance between adjacent branch-axis slots; uses the renderer default when unset.",
    )
    margin_commit_axis_lower: NonNegativeFloat | None = Field(
        default=None,
        description="Pinned commit-axis margin at the oldest-commit end; auto-fit when unset.",
    )
    margin_commit_axis_upper: NonNegativeFloat | None = Field(
        default=None,
        description="Pinned commit-axis margin at the newest-commit end; auto-fit when unset.",
    )
    margin_branch_axis_lower: NonNegativeFloat | None = Field(
        default=None,
        description="Pinned branch-axis margin at the lane-0 end; auto-fit when unset.",
    )
    margin_branch_axis_upper: NonNegativeFloat | None = Field(
        default=None,
        description="Pinned branch-axis margin at the highest-lane end; auto-fit when unset.",
    )
