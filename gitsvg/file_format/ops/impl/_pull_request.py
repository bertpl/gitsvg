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
    id: IdStr | None = None
    from_: IdStr = Field(alias="from")
    into: IdStr
    title: NonEmptyStr | None = None
