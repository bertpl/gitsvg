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

Encapsulation contract: `Occupancy`'s storage is private. Callers only
ever see `bool`, `frozenset[int]`, `list[int]`, or `tuple[int, int]`
values through the public API. Storage can swap to an owner-aware
shape (e.g. `dict[int, dict[int, Owner]]` with `add(lane, row,
owner=...)` and `what_owns(lane, row)`) without changing any existing
call site.
"""

from collections.abc import Iterator


# ==================================================================================================
#  Occupancy
# ==================================================================================================
class Occupancy:
    """Lane-keyed set of occupied (branch_pos, commit_pos) points.

    Storage today is one set of rows per lane. The public API is shaped
    so an owner-aware extension (`add(lane, row, owner=...)`,
    `what_owns(lane, row)`) can be added later without changing any
    existing call site.
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
    def is_occupied(self, branch_pos: int, commit_pos: int) -> bool:
        """Return True iff `(branch_pos, commit_pos)` has been registered."""
        rows = self._rows_by_lane.get(branch_pos)
        return rows is not None and commit_pos in rows

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

    def occupied_rows_on(self, branch_pos: int) -> frozenset[int]:
        """Return all occupied rows on `branch_pos` as a frozen set."""
        rows = self._rows_by_lane.get(branch_pos)
        return frozenset(rows) if rows is not None else frozenset()

    def occupied_lanes(self) -> list[int]:
        """Return every lane with at least one occupied row, sorted ascending."""
        return sorted(self._rows_by_lane.keys())

    # --------------------------------------------------------------------------
    #  Iteration
    # --------------------------------------------------------------------------
    def __iter__(self) -> Iterator[tuple[int, int]]:
        """Yield every occupied `(branch_pos, commit_pos)` point.

        Iteration order is sorted by lane, then by row — deterministic
        regardless of insertion order.
        """
        for lane in sorted(self._rows_by_lane.keys()):
            for row in sorted(self._rows_by_lane[lane]):
                yield (lane, row)
