"""The `import` operation."""

from typing import Literal

from pydantic import Field

from gitsvg.file_format.ops.framework._base import OpBase
from gitsvg.file_format.ops.framework._types import NonEmptyStr


class ImportOp(OpBase):
    """Replay another file as a prelude before applying further ops.

    Must be the first op in the file when present. Cycle detection
    runs on resolved absolute paths; nesting is capped at depth 1000.
    """

    op: Literal["import"]
    path: NonEmptyStr = Field(
        description="Path to another `.gitsvg.jsonl` file, resolved relative to the file containing the import op.",
    )
