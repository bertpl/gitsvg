"""The `remove` operation."""

from typing import Literal, Self

from pydantic import Field, model_validator

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import IdStr


class RemoveOp(OpBase):
    """Delete one or more commits, branches, or pull-requests from current state.

    Exactly one kind-specific list field (`commits`, `branches`, or
    `pull_requests`) must be set per op.
    """

    op: Literal["remove"]
    commits: list[IdStr] | None = Field(
        default=None,
        min_length=1,
        description="Commit ids to drop from state. Each id is also removed from its branch's commit list.",
    )
    branches: list[IdStr] | None = Field(
        default=None,
        min_length=1,
        description=(
            "Branch names to drop from state; cascades to every commit on each branch. "
            "Blocked if any open pull-request still references the branch."
        ),
    )
    pull_requests: list[IdStr] | None = Field(
        default=None,
        min_length=1,
        description=(
            "Pull-request ids to close. Use this before a `merge` for the same `(from, into)` pair "
            "or a branch removal that would otherwise orphan the PR."
        ),
    )

    @model_validator(mode="after")
    def _validate_exactly_one_kind(self) -> Self:
        """Require exactly one of `commits`, `branches`, or `pull_requests` to be set."""
        n_set = sum(field is not None for field in (self.commits, self.branches, self.pull_requests))
        if n_set != 1:
            raise ValueError("remove op must specify exactly one of 'commits', 'branches', or 'pull_requests'")
        return self
