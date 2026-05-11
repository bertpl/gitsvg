"""The `highlight` operation."""

from typing import Literal

from pydantic import Field

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import IdStr


class HighlightOp(OpBase):
    """Mark an existing commit as highlighted (renders with an enlarged dot and a bold message label)."""

    op: Literal["highlight"]
    commit: IdStr = Field(description="Commit id to highlight; must reference an existing commit in current state.")
