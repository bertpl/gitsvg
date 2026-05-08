"""The `merge` operation."""

from typing import Literal

from pydantic import Field

from gitsvg._format.ops._framework._base import OpBase


class MergeOp(OpBase):
    """Two-parent commit on `into`, with an arc back to the tip of `from`."""

    op: Literal["merge"]
    from_: str = Field(alias="from")
    into: str
    as_: str | None = Field(default=None, alias="as")
    msg: str | None = None
