"""The `import` operation."""

from typing import Literal

from gitsvg._file_format.ops._framework._base import OpBase
from gitsvg._file_format.ops._framework._types import NonEmptyStr


class ImportOp(OpBase):
    """Replay another file as a prelude before applying further ops."""

    op: Literal["import"]
    path: NonEmptyStr
