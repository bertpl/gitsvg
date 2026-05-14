"""Discriminated union and registries for the seven operations.

The `op:` field on each model is a `Literal[<name>]` and serves as the
discriminator. Downstream code should prefer `OP_ADAPTER` (a pydantic
`TypeAdapter`) over instantiating individual op classes manually — the
adapter dispatches on `op:` and returns the correct subclass.
"""

from typing import Annotated, Union, get_args

from pydantic import BaseModel, Field, TypeAdapter

from gitsvg.file_format.ops.impl._branch import BranchOp
from gitsvg.file_format.ops.impl._commit import CommitOp
from gitsvg.file_format.ops.impl._grid import GridOp
from gitsvg.file_format.ops.impl._highlight import HighlightOp
from gitsvg.file_format.ops.impl._import import ImportOp
from gitsvg.file_format.ops.impl._merge import MergeOp
from gitsvg.file_format.ops.impl._pull_request import PullRequestOp
from gitsvg.file_format.ops.impl._remove import RemoveOp
from gitsvg.file_format.ops.impl._theme import ThemeOp

# ==================================================================================================
#  Op type registry — single source of truth for the op set
# ==================================================================================================
ALL_OP_TYPES: list[type[BaseModel]] = [
    ImportOp,
    GridOp,
    ThemeOp,
    BranchOp,
    CommitOp,
    MergeOp,
    PullRequestOp,
    RemoveOp,
    HighlightOp,
]


def _op_name(model_cls: type[BaseModel]) -> str:
    """Return the literal value of a model's `op` discriminator field.

    Args:
        model_cls: An op model class with an `op: Literal["<name>"]` field.

    Returns:
        The single literal string the `op` field is annotated with.
    """
    annotation = model_cls.model_fields["op"].annotation
    return get_args(annotation)[0]


OP_BY_NAME: dict[str, type[BaseModel]] = {_op_name(cls): cls for cls in ALL_OP_TYPES}


OP_NAMES: list[str] = list(OP_BY_NAME.keys())


# ==================================================================================================
#  Discriminated union + adapter
# ==================================================================================================
OpUnion = Annotated[
    Union[
        ImportOp,
        GridOp,
        ThemeOp,
        BranchOp,
        CommitOp,
        MergeOp,
        PullRequestOp,
        RemoveOp,
        HighlightOp,
    ],
    Field(discriminator="op"),
]


OP_ADAPTER: TypeAdapter = TypeAdapter(OpUnion)
