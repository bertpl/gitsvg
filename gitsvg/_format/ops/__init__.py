"""Pydantic models for the seven v0.0.x gitsvg operations.

Subpackage layout:

- `_framework/` — `OpBase` and the discriminated union + registries.
- `_impl/` — one pydantic model per operation.

External callers should import from this package directly.
"""

from gitsvg._format.ops._framework import (
    ALL_OP_TYPES,
    OP_ADAPTER,
    OP_BY_NAME,
    OP_NAMES,
    OpBase,
    OpUnion,
)
from gitsvg._format.ops._impl import (
    BranchOp,
    CanvasOp,
    CommitOp,
    HighlightOp,
    ImportOp,
    MergeOp,
    RemoveOp,
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
    "OpBase",
    "OpUnion",
    "RemoveOp",
]
