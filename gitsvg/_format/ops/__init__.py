"""Pydantic models for the seven v0.0.x gitsvg operations.

Each module under this package defines one operation model. The
discriminated union and registries live in `_union`.
"""

from gitsvg._format.ops._branch import BranchOp
from gitsvg._format.ops._canvas import CanvasOp
from gitsvg._format.ops._commit import CommitOp
from gitsvg._format.ops._highlight import HighlightOp
from gitsvg._format.ops._import import ImportOp
from gitsvg._format.ops._merge import MergeOp
from gitsvg._format.ops._remove import RemoveOp
from gitsvg._format.ops._union import (
    ALL_OP_TYPES,
    OP_ADAPTER,
    OP_BY_NAME,
    OP_NAMES,
    OpUnion,
)

__all__ = [
    "ALL_OP_TYPES",
    "BranchOp",
    "CanvasOp",
    "CommitOp",
    "HighlightOp",
    "ImportOp",
    "MergeOp",
    "OP_ADAPTER",
    "OP_BY_NAME",
    "OP_NAMES",
    "OpUnion",
    "RemoveOp",
]
