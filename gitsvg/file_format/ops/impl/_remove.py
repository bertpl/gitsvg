"""The `remove` operation."""

from typing import Literal, Self

from pydantic import Field, model_validator

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import IdStr


class RemoveOp(OpBase):
    """Delete one or more commits or branches from current state.

    Exactly one kind-specific list field (`commits` or `branches`)
    must be set per op.
    """

    op: Literal["remove"]
    commits: list[IdStr] | None = Field(default=None, min_length=1)
    branches: list[IdStr] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _validate_exactly_one_kind(self) -> Self:
        """Require exactly one of `commits` or `branches` to be set."""
        n_set = sum(field is not None for field in (self.commits, self.branches))
        if n_set != 1:
            raise ValueError("remove op must specify exactly one of 'commits' or 'branches'")
        return self
