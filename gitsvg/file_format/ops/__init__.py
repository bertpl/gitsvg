"""Pydantic models for the seven v0.0.x gitsvg operations.

Subpackage layout:

- `framework/` — `OpBase` and the discriminated union + registries.
- `impl/` — one pydantic model per operation.

External callers should import from this package directly.
"""

from gitsvg.file_format.ops.framework import (
    ALL_OP_TYPES,
    OP_ADAPTER,
    OP_BY_NAME,
    OP_NAMES,
    OpBase,
    OpUnion,
)
from gitsvg.file_format.ops.impl import (
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
