"""MergeCommitStyle enum — how a merge commit's dot is drawn.

Selected by `theme.merge_commit_style` and applied to every merge commit
(ordinary commits always use the plain `circle` dot). Members carry their
canonical string value so the enum interoperates with Pydantic / JSON and
with raw-string comparison, mirroring `Orientation` / `BranchLineStyle`.
"""

from enum import StrEnum


class MergeCommitStyle(StrEnum):
    """Merge-commit dot style.

    - `CIRCLE`: the plain commit dot — branch-color fill,
      `commit_stroke_color` outline (the default; identical to an ordinary
      commit).
    - `CHECKMARK`: a hollow dot — fill and stroke swap (fill =
      `commit_stroke_color`, stroke = the branch color) with a branch-color
      checkmark, marking the commit as a merge at a glance.
    """

    CIRCLE = "circle"
    CHECKMARK = "checkmark"
