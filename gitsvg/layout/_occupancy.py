"""Lane-keyed occupancy tracking for the layout engine.

The occupancy model in one sentence: a *set of points* (`branch_pos`,
`commit_pos`) per lane. A point is a cell claimed by some visible
element. Asking "is this lane blocked at or after row T?" is the core
question the lane-assignment heuristic asks; that threshold form is
what the engine consumes today.

What contributes to occupancy:

- Every commit on a branch — at `(branch.branch_pos, commit.commit_pos)`.
- Every empty branch — a single pseudo-point at `(branch.branch_pos,
  branch.start)`. Captures "the branch exists on this lane, even if it
  has no commits yet."

What does **not** contribute:

- Branch lines (vertical segments between `start` and `end`). Only the
  commits and pseudo-starts on the lane count.
- Branch-off arcs and merge arcs — they cross lanes but don't reserve
  cells on them.
- Branch-name pills, commit labels, hash labels — visual chrome, not
  layout-blocking.
- Pull-request elements: the dashed arc-and-line, the horizontal
  segment, and the optional title pill. Same posture as their merge
  counterparts — visible-but-non-blocking. A PR's projected merge row
  *does* show up in the canvas auto-fit calculation (so the diagram
  has room to draw it) but it does not occupy a lane cell.

Encapsulation contract: `Occupancy`'s storage is private — callers
interact only through `add` and the `is_blocked_at_or_after` query,
never touching the underlying per-lane sets.
"""


# ==================================================================================================
#  Occupancy
# ==================================================================================================
class Occupancy:
    """Lane-keyed set of occupied (branch_pos, commit_pos) points.

    Backed by one set of rows per lane. Callers register points with
    `add` and ask whether a lane is blocked at or beyond a row with
    `is_blocked_at_or_after`.
    """

    # --------------------------------------------------------------------------
    #  Initialization
    # --------------------------------------------------------------------------
    def __init__(self) -> None:
        """Construct an empty occupancy."""
        self._rows_by_lane: dict[int, set[int]] = {}

    # --------------------------------------------------------------------------
    #  Writes
    # --------------------------------------------------------------------------
    def add(self, branch_pos: int, commit_pos: int) -> None:
        """Register `(branch_pos, commit_pos)` as occupied.

        Idempotent — adding the same point twice is a no-op.

        Args:
            branch_pos: Lane index along the branch axis.
            commit_pos: Row index along the commit axis.
        """
        self._rows_by_lane.setdefault(branch_pos, set()).add(commit_pos)

    # --------------------------------------------------------------------------
    #  Queries
    # --------------------------------------------------------------------------
    def is_blocked_at_or_after(self, branch_pos: int, threshold: int) -> bool:
        """Return True iff any occupied row on `branch_pos` is at or above `threshold`.

        This is the core question the lane-assignment heuristic asks
        when looking for a free lane for a new branch.

        Args:
            branch_pos: Lane index to inspect.
            threshold: Row index threshold.

        Returns:
            `True` if any registered point on `branch_pos` has
            `commit_pos >= threshold`, else `False`.
        """
        rows = self._rows_by_lane.get(branch_pos)
        if rows is None:
            return False
        return any(row >= threshold for row in rows)
