"""Layout engine — assign axis positions to every branch and commit.

`compute_layout(parsed_ops)` walks an op stream in source order and
builds a `Layout`. The walk mirrors the state engine's bookkeeping
just enough to:

- Generate the same auto-ids the state engine generates (so layout
  positions can be looked up by the same commit ids state uses).
- Track each branch's commit-axis tip and commit list, which is what
  drives subsequent commits' positions.

Heuristics applied (per the v0.0.3 layout decisions):

- **Branch axis.** Branches get monotonically incrementing positions
  in declaration order. Lane-reuse heuristics are deferred.
- **Branch start (commit axis).** A new branch is rooted at
  `parent_commit.commit_pos + 1`, where `parent_commit` is the commit
  resolved from `from_commit:` directly or from `from_branch:`'s tip
  at the moment the `branch` op runs. The first declared branch
  starts at 0.
- **Commit on a branch.** First commit lands at `start + gap`;
  subsequent commits at `tip + 1 + gap`. Equivalently, the branch
  has a `next_commit_pos` initialised to `start`; each commit places
  at `next_commit_pos + gap`, then advances by one.
- **Merge commit.** Lands on the `into` branch at
  `max(into.tip, from.tip) + 1 + gap`, always above both parents.
- **`replaces:` commit.** Takes the position of the *first* replaced
  commit; the replaced commits are removed; the branch's tip rolls
  back to the new commit. (`gap:` is rejected on `replaces:` commits
  by the schema layer; the engine therefore never sees both at once.)
- **`remove`.** Removes commits/branches from the layout. The branch
  axis is not compacted (lane-reuse is v0.0.4).

The walker treats `import`, `canvas`, and `highlight` as no-ops for
layout — `import` is already expanded upstream; `canvas` is consumed
elsewhere; `highlight` toggles a visual flag without affecting
positions.
"""

from dataclasses import dataclass, field

from gitsvg.file_format.ops import (
    BranchOp,
    CanvasOp,
    CommitOp,
    HighlightOp,
    ImportOp,
    MergeOp,
    RemoveOp,
)
from gitsvg.layout._layout import Layout, LayoutBranch, LayoutCommit
from gitsvg.parse import ParsedOp


def compute_layout(parsed_ops: list[ParsedOp]) -> Layout:
    """Compute a `Layout` from a stream of parsed ops.

    Assumes `parsed_ops` has been schema- and semantically validated
    (e.g. by `gitsvg.state.apply_ops`) and that `import` ops are
    already expanded by `gitsvg.imports.resolve_imports`. Layout does
    not re-validate; ill-formed inputs may produce inconsistent
    positions.

    Args:
        parsed_ops: Ops in source order, with imports already
            expanded.

    Returns:
        A `Layout` mapping each branch and commit to axis positions.
    """
    builder = _LayoutBuilder()
    for parsed in parsed_ops:
        builder.handle(parsed.op)
    return builder.layout


# ==================================================================================================
#  Internal walker
# ==================================================================================================
@dataclass(slots=True)
class _BranchTracker:
    """Per-branch bookkeeping during layout computation.

    Tracks the commit-axis position the next commit on this branch
    will land at, and the ordered list of commit ids currently
    attached to the branch (for tip lookup and replaces/remove
    handling).
    """

    name: str
    branch_pos: int
    start: int
    next_commit_pos: int
    commit_ids: list[str] = field(default_factory=list)

    def tip_id(self) -> str | None:
        """Return the most recently attached commit id, or None when empty."""
        return self.commit_ids[-1] if self.commit_ids else None


class _LayoutBuilder:
    """Walks parsed ops, mutating a `Layout` plus per-branch trackers.

    Public surface is `handle(op)` — call once per parsed op in source
    order. After the walk, `self.layout` holds the result.
    """

    def __init__(self) -> None:
        """Initialise an empty layout and zeroed counters."""
        self.layout = Layout()
        self._next_branch_pos: int = 0
        self._trackers: dict[str, _BranchTracker] = {}
        self._commit_branch: dict[str, str] = {}
        self._auto_id_counter: int = 1

    # --------------------------------------------------------------------------
    #  Dispatch
    # --------------------------------------------------------------------------
    def handle(self, op: object) -> None:
        """Dispatch a single op to its layout-aware handler."""
        if isinstance(op, BranchOp):
            self._handle_branch(op)
        elif isinstance(op, CommitOp):
            self._handle_commit(op)
        elif isinstance(op, MergeOp):
            self._handle_merge(op)
        elif isinstance(op, RemoveOp):
            self._handle_remove(op)
        elif isinstance(op, (HighlightOp, CanvasOp, ImportOp)):
            return  # no layout effect

    # --------------------------------------------------------------------------
    #  Branch
    # --------------------------------------------------------------------------
    def _handle_branch(self, op: BranchOp) -> None:
        """Place a new branch on the next free branch-axis slot."""
        is_first = not self._trackers
        start = self._resolve_branch_start(op, is_first=is_first)

        branch_pos = self._next_branch_pos
        self._next_branch_pos += 1

        self.layout.branches[op.name] = LayoutBranch(
            name=op.name,
            branch_pos=branch_pos,
            start=start,
            end=start,
        )
        self._trackers[op.name] = _BranchTracker(
            name=op.name,
            branch_pos=branch_pos,
            start=start,
            next_commit_pos=start,
        )

    def _resolve_branch_start(self, op: BranchOp, *, is_first: bool) -> int:
        """Compute the branch-axis-perpendicular start position for a new branch."""
        if is_first:
            return 0
        if op.from_commit is not None:
            return self.layout.commits[op.from_commit].commit_pos + 1
        if op.from_branch is not None:
            parent_tracker = self._trackers[op.from_branch]
            tip = parent_tracker.tip_id()
            if tip is not None:
                return self.layout.commits[tip].commit_pos + 1
            # Parent branch has no commits — root the new branch at the parent's start.
            return self.layout.branches[op.from_branch].start + 1
        # Defensive fallback — semantic validation rejects this case upstream.
        return 0

    # --------------------------------------------------------------------------
    #  Commit
    # --------------------------------------------------------------------------
    def _handle_commit(self, op: CommitOp) -> None:
        """Place a new commit on its branch (or a `replaces:` squash commit)."""
        commit_id = op.id if op.id is not None else self._next_auto_commit_id()
        gap = op.gap or 0
        replaces = op.replaces or []
        tracker = self._trackers[op.branch]

        if replaces:
            commit_pos = self._handle_replaces(tracker, replaces)
        else:
            commit_pos = tracker.next_commit_pos + gap

        tracker.next_commit_pos = commit_pos + 1
        tracker.commit_ids.append(commit_id)
        self._commit_branch[commit_id] = op.branch

        self.layout.commits[commit_id] = LayoutCommit(
            id=commit_id,
            branch_pos=tracker.branch_pos,
            commit_pos=commit_pos,
        )
        self._refresh_branch_end(op.branch)

    def _handle_replaces(self, tracker: _BranchTracker, replaces: list[str]) -> int:
        """Drop the replaced commits and return the position the new commit takes."""
        first_replaced_pos = self.layout.commits[replaces[0]].commit_pos
        for rid in replaces:
            self._drop_commit(rid, tracker)
        return first_replaced_pos

    # --------------------------------------------------------------------------
    #  Merge
    # --------------------------------------------------------------------------
    def _handle_merge(self, op: MergeOp) -> None:
        """Place a merge commit above both parent tips."""
        merge_id = op.as_ if op.as_ is not None else self._next_auto_commit_id()
        gap = op.gap or 0
        into_tracker = self._trackers[op.into]
        from_tracker = self._trackers[op.from_]

        into_tip_pos = self._tip_pos(into_tracker)
        from_tip_pos = self._tip_pos(from_tracker)
        commit_pos = max(into_tip_pos, from_tip_pos) + 1 + gap

        into_tracker.next_commit_pos = commit_pos + 1
        into_tracker.commit_ids.append(merge_id)
        self._commit_branch[merge_id] = op.into

        self.layout.commits[merge_id] = LayoutCommit(
            id=merge_id,
            branch_pos=into_tracker.branch_pos,
            commit_pos=commit_pos,
        )
        self._refresh_branch_end(op.into)

    def _tip_pos(self, tracker: _BranchTracker) -> int:
        """Return the commit-axis position of `tracker`'s tip, or `start - 1` if empty."""
        tip = tracker.tip_id()
        if tip is not None:
            return self.layout.commits[tip].commit_pos
        return tracker.start - 1

    # --------------------------------------------------------------------------
    #  Remove
    # --------------------------------------------------------------------------
    def _handle_remove(self, op: RemoveOp) -> None:
        """Remove commits or a branch (and cascade) from the layout.

        Lane-reuse / branch-axis compaction is intentionally not done
        here — the seed corpus's lane-reuse patterns are deferred to
        v0.0.4. Removing a branch leaves its `branch_pos` slot
        unoccupied; subsequent branches keep getting incremented
        positions.
        """
        if op.commits:
            for cid in op.commits:
                tracker_name = self._commit_branch.get(cid)
                if tracker_name is None:
                    continue
                self._drop_commit(cid, self._trackers[tracker_name])
                self._refresh_branch_end(tracker_name)
        elif op.branches:
            for bname in op.branches:
                self._drop_branch(bname)

    def _drop_branch(self, name: str) -> None:
        """Remove a branch and cascade-remove all its commits."""
        tracker = self._trackers.pop(name, None)
        if tracker is None:
            return
        for cid in list(tracker.commit_ids):
            self.layout.commits.pop(cid, None)
            self._commit_branch.pop(cid, None)
        self.layout.branches.pop(name, None)

    # --------------------------------------------------------------------------
    #  Shared helpers
    # --------------------------------------------------------------------------
    def _drop_commit(self, commit_id: str, tracker: _BranchTracker) -> None:
        """Remove a commit from `layout.commits` and from `tracker.commit_ids`."""
        self.layout.commits.pop(commit_id, None)
        self._commit_branch.pop(commit_id, None)
        if commit_id in tracker.commit_ids:
            tracker.commit_ids.remove(commit_id)

    def _refresh_branch_end(self, branch_name: str) -> None:
        """Recompute `LayoutBranch.end` from the branch's current commit list."""
        tracker = self._trackers[branch_name]
        branch = self.layout.branches[branch_name]
        if tracker.commit_ids:
            branch.end = max(self.layout.commits[cid].commit_pos for cid in tracker.commit_ids)
        else:
            branch.end = branch.start

    def _next_auto_commit_id(self) -> str:
        """Return the lowest `_c<N>` not already used by any commit in the layout."""
        while f"_c{self._auto_id_counter}" in self.layout.commits:
            self._auto_id_counter += 1
        cid = f"_c{self._auto_id_counter}"
        self._auto_id_counter += 1
        return cid
