"""The `pull_request` operation."""

from typing import Literal

from pydantic import Field

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import IdStr, NonEmptyStr


class PullRequestOp(OpBase):
    """Declare a pending merge — a visual indicator that `from` is proposed to merge into `into`.

    Both endpoints live-track the current tips of the two branches at
    render time, so new commits on either side push the PR's arc
    forward. A `pull_request` does not add a commit on either branch;
    it persists in state until explicitly removed via a `remove` op
    with a matching `pull_requests:` entry.
    """

    op: Literal["pull_request"]
    id: IdStr | None = Field(
        default=None,
        description=(
            "Explicit pull-request id; auto-generated as `_prN` when omitted. "
            "Set explicitly if a later `remove` op will reference this PR."
        ),
    )
    from_: IdStr = Field(
        alias="from",
        description="Source branch the pull-request proposes to merge.",
    )
    into: IdStr = Field(
        description="Target branch the pull-request proposes merging into.",
    )
    title: NonEmptyStr | None = Field(
        default=None,
        description="Short headline label rendered next to the PR arc; omit for an unlabelled PR.",
    )
