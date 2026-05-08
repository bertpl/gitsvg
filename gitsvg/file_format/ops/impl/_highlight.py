"""The `highlight` operation."""

from typing import Literal

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import IdStr


class HighlightOp(OpBase):
    """Mark an existing commit as highlighted (renders with a halo)."""

    op: Literal["highlight"]
    commit: IdStr
