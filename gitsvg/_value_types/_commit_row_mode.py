"""CommitRowMode enum — whether commits may share a commit-axis row.

Selected by `theme.commit_row_mode` and consumed by the layout engine
(via `LayoutSettings`) when it assigns each commit its `commit_pos`.
Members carry their canonical string value so the enum interoperates
with Pydantic / JSON and with raw-string comparison, mirroring
`Orientation` / `BranchLineStyle`.
"""

from enum import StrEnum


class CommitRowMode(StrEnum):
    """How the layout engine packs commits along the commit axis.

    - `SHARED`: commits on different branches may share a `commit_pos`
      row (the default) — compact, but a row can hold unrelated commits.
    - `UNIQUE`: every commit gets its own row, assigned in authoring
      (declaration) order, so vertical position strictly encodes the
      order events were declared.
    """

    SHARED = "shared"
    UNIQUE = "unique"
