"""LayoutArcKind enum — what kind of connector a `LayoutArc` represents.

Carried explicitly on `LayoutArc` so the renderer and the serializer can
dispatch on the connector's role rather than re-deriving it from
geometry. Geometry alone cannot distinguish every kind: a lane-change
connector has both endpoints on the same branch one row apart, so the
"branch point above the trunk ⇒ branch-off, at or below ⇒ merge" test
would misclassify it. Members carry their canonical string value so the
enum interoperates with JSON and raw-string comparison, mirroring
`Orientation` / `BranchLineStyle` / `CommitRowMode`.
"""

from enum import StrEnum


class LayoutArcKind(StrEnum):
    """What a `LayoutArc` connects.

    - `BRANCH_OFF`: parent commit on an ongoing branch → the start of a
      new branch.
    - `MERGE`: a merge commit → the merged-in tip on another lane.
    - `LANE_CHANGE`: one branch's own line stepping between two lanes
      across a single row (emitted only when lane migration is active).
    """

    BRANCH_OFF = "branch_off"
    MERGE = "merge"
    LANE_CHANGE = "lane_change"
