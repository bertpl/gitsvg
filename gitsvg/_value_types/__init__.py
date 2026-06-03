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
the package: `from gitsvg._value_types import Orientation`.
"""

from gitsvg._value_types._box_anchor import BoxAnchor, validate_box_anchor
from gitsvg._value_types._branch_line_style import BranchLineStyle
from gitsvg._value_types._commit_label_layout import CommitLabelLayout
from gitsvg._value_types._commit_row_mode import CommitRowMode
from gitsvg._value_types._label_side import LabelSide
from gitsvg._value_types._merge_commit_style import MergeCommitStyle
from gitsvg._value_types._orientation import Orientation, normalize_orientation

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
