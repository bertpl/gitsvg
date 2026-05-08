"""The `highlight` operation."""

from typing import Literal

from gitsvg._format.ops._framework._base import OpBase


class HighlightOp(OpBase):
    """Mark an existing commit as highlighted (renders with a halo)."""

    op: Literal["highlight"]
    commit: str
