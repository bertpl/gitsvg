"""The `grid` operation."""

from typing import Literal

from pydantic import Field

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import NonNegativeInt


class GridOp(OpBase):
    """Pin the integer-grid extent (slot counts only); default is auto-fit.

    The grid op carries the two layout-engine inputs that don't have
    natural defaults from the content. Spacing, margins, and every
    other pixel-side concern live on `theme:` instead — see invariant
    #6 in `docs/architecture.md`.
    """

    op: Literal["grid"]
    n_commits: NonNegativeInt | None = Field(
        default=None,
        description="Pinned commit-axis slot count; auto-fit from content when unset.",
    )
    n_branches: NonNegativeInt | None = Field(
        default=None,
        description="Pinned branch-axis slot count; auto-fit from content when unset.",
    )
