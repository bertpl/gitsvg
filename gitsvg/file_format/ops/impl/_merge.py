"""The `merge` operation."""

from typing import Literal

from pydantic import Field

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import IdStr, NonEmptyStr


class MergeOp(OpBase):
    """Two-parent commit on `into`, with an arc back to the tip of `from`."""

    op: Literal["merge"]
    from_: IdStr = Field(alias="from")
    into: IdStr
    as_: IdStr | None = Field(default=None, alias="as")
    msg: NonEmptyStr | None = None
