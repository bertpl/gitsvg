"""CommitLabelLayout enum — how commit labels are placed relative to the graph.

Selected by `theme.commit_label_layout`. `inline` places each commit's
`msg` / `hash` beside its own dot, anchored per-commit (the default);
`table` routes the commit metadata into a fixed-column table beside the
graph, one row per commit. `table` is meaningful only in vertical
orientations and implies one commit per commit-axis row
(`commit_row_mode: unique`). Members carry their canonical string value so
the enum interoperates with Pydantic / JSON and raw-string comparison,
mirroring `CommitRowMode` / `Orientation`.
"""

from enum import StrEnum


class CommitLabelLayout(StrEnum):
    """How commit labels are placed relative to the graph.

    - `INLINE`: each commit's `msg` / `hash` are placed beside its own
      dot, anchored per-commit (the default).
    - `TABLE`: commit metadata is laid out as fixed-width columns beside
      the graph, one row per commit. Vertical orientations only; implies
      `commit_row_mode: unique`.
    """

    INLINE = "inline"
    TABLE = "table"
