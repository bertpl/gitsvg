"""BranchLineStyle enum — the shape of the connectors between lanes.

Selected by `theme.branch_line_style` and applied uniformly to every
connector (branch-off, merge, pull-request). Members carry their
canonical string value so the enum interoperates with Pydantic / JSON
and with raw-string comparison, mirroring `Orientation`.
"""

from enum import StrEnum


class BranchLineStyle(StrEnum):
    """Connector shape between two lanes.

    - `ROUNDED`: two straight legs joined by a single quarter-arc corner
      (the default).
    - `STRAIGHT`: a direct line, no arc.
    - `BEZIER`: a smooth cubic-Bézier S, tangent to the commit axis at both
      ends.
    - `DOUBLE_ROUNDED`: a stepped connector — two quarter-arcs around an
      orthogonal crossing near the trunk, then a parallel run to the branch.
    """

    ROUNDED = "rounded"
    STRAIGHT = "straight"
    BEZIER = "bezier"
    DOUBLE_ROUNDED = "double_rounded"
