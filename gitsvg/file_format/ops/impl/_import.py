"""The `import` operation."""

from typing import Literal

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import NonEmptyStr


class ImportOp(OpBase):
    """Replay another file as a prelude before applying further ops."""

    op: Literal["import"]
    path: NonEmptyStr
