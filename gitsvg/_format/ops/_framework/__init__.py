"""Framework-level constructs for the ops package.

`OpBase` is the shared pydantic configuration; `_union` builds the
discriminated union and registries from the op classes in `_impl`.

Op-implementation modules under `_impl` must import `OpBase` via the
leaf path (`gitsvg._format.ops._framework._base`), not via this
package, to avoid circular imports during `_union` loading.
"""

from gitsvg._format.ops._framework._base import OpBase
from gitsvg._format.ops._framework._union import (
    ALL_OP_TYPES,
    OP_ADAPTER,
    OP_BY_NAME,
    OP_NAMES,
    OpUnion,
)

__all__ = [
    "ALL_OP_TYPES",
    "OP_ADAPTER",
    "OP_BY_NAME",
    "OP_NAMES",
    "OpBase",
    "OpUnion",
]
