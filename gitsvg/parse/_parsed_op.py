"""ParsedOp — an op model paired with its source location."""

from dataclasses import dataclass

from gitsvg.file_format.ops import OpBase


@dataclass(frozen=True, slots=True)
class ParsedOp:
    """An op model paired with the file path and line number it was parsed from.

    Attributes:
        op: The validated pydantic op model.
        file: Source file path the op was parsed from.
        line: 1-based line number within `file`.
    """

    op: OpBase
    file: str
    line: int
