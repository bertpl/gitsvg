"""Shared presentational value-types — the vocabulary of presentational choices.

Dependency-free leaf package: every type here is a plain `StrEnum` or a
tuple alias built on the standard library alone, so this package imports
nothing from the rest of `gitsvg`. `file_format`, `theme`, `layout`, and
`render` all import these types one-way from here, which keeps the
value-type vocabulary off the inter-package import edges — in particular
it breaks the `file_format` ↔ `theme` cycle that arose when these types
lived inside `theme/` while `theme` imported `LabelSide` back from
`file_format`.

Each type keeps its own submodule (mirroring the one-type-per-file
layout used elsewhere) and is re-exported here, so callers import from
the package: `from gitsvg._shared.value_types import Orientation`.
"""

from ._box_anchor import BoxAnchor, validate_box_anchor
from ._branch_line_style import BranchLineStyle
from ._commit_label_layout import CommitLabelLayout
from ._commit_row_mode import CommitRowMode
from ._label_side import LabelSide
from ._merge_commit_style import MergeCommitStyle
from ._orientation import Orientation, normalize_orientation

__all__ = [
    "BoxAnchor",
    "BranchLineStyle",
    "CommitLabelLayout",
    "CommitRowMode",
    "LabelSide",
    "MergeCommitStyle",
    "Orientation",
    "normalize_orientation",
    "validate_box_anchor",
]
