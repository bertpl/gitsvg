"""The `remove` operation."""

from typing import Literal

from gitsvg._format.ops._base import OpBase


class RemoveOp(OpBase):
    """Delete one or more commits or branches from current state.

    Exactly one kind-specific list field (`commits` or `branches`) must
    be set; that constraint is enforced at the per-op semantic phase
    (PR4), not at shape level.
    """

    op: Literal["remove"]
    commits: list[str] | None = None
    branches: list[str] | None = None
