"""The `branch` operation."""

from typing import Literal, Self

from pydantic import Field, model_validator

from gitsvg.file_format._label_side import LabelSide
from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import HexColor, IdStr, NonNegativeInt


class BranchOp(OpBase):
    """Declare a branch (optionally rooted on another branch's tip or a commit)."""

    op: Literal["branch"]
    name: IdStr = Field(description="Unique branch name.")
    # Two distinct root sources can't share one `from` key, so `branch` uses
    # bare `from_branch` / `from_commit` rather than the `from`/`into` alias
    # pattern that `MergeOp` / `PullRequestOp` follow. The split is intentional.
    from_branch: IdStr | None = Field(
        default=None,
        description="Source branch this branch is rooted on (mutually exclusive with `from_commit`).",
    )
    from_commit: IdStr | None = Field(
        default=None,
        description="Source commit this branch is rooted on (mutually exclusive with `from_branch`).",
    )
    color: HexColor | None = Field(
        default=None,
        description="Override hex color for this branch; cycles through defaults when unset.",
    )
    label_side: LabelSide | None = Field(
        default=None,
        description="Branch-axis-index side commit labels render on (`before` = lower-index side; `after` = higher-index side). Orientation-invariant; the renderer maps to a pixel side per `theme.orientation`.",
    )
    branch_pos: NonNegativeInt | None = Field(
        default=None,
        description="Override lane index for this branch; bypasses the lane-reuse heuristic.",
    )

    @model_validator(mode="after")
    def _validate_at_most_one_root(self) -> Self:
        """Reject specifying both `from_branch` and `from_commit`."""
        if self.from_branch is not None and self.from_commit is not None:
            raise ValueError("'from_branch' and 'from_commit' are mutually exclusive on a branch op")
        return self
