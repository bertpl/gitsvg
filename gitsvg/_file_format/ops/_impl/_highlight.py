"""The `highlight` operation."""

from typing import Literal

from gitsvg._file_format.ops._framework._base import OpBase
from gitsvg._file_format.ops._framework._types import IdStr


class HighlightOp(OpBase):
    """Mark an existing commit as highlighted (renders with a halo)."""

    op: Literal["highlight"]
    commit: IdStr
