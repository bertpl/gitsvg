"""Layout dataclasses — the integer-grid intermediate representation.

Produced by `gitsvg.layout.compute_layout(state)` from a fully-built
`State`, consumed by `gitsvg.render.render(layout, theme)`. The
layout is *exclusively* about integer-grid positioning:

- `branch_pos` / `commit_pos` slot indices for every entity.
- Semantic identifiers (branch `id`, commit `id`, PR `id`).
- Resolved hash strings (auto-resolved 7-char hex from state).
- Pre-computed connectors as a `trunk_point` / `branch_point` slot pair
  each (branch-off and merge); the renderer derives elbow orientation,
  draw direction, and colour attribution from the two points.
- Grid extent (`n_commits`, `n_branches`).

Layout output carries **no** colour, pixel, font, stroke, opacity,
render-strategy, or presentational-override data. Every presentational
decision happens in the renderer from the resolved `Theme` — colour
attribution and segment-draw-order for arcs, per-branch label-side
resolution, and so on.

Different layout strategies (default declaration-order assignment,
lane-reuse, future left-to-right orientations) all produce the same
`Layout` schema, so the renderer stays oblivious.
"""

from dataclasses import dataclass, field

from gitsvg.layout._layout_arc_kind import LayoutArcKind


@dataclass(slots=True)
class GridSlot:
    """One slot on the integer grid — a (branch-axis, commit-axis) index pair.

    Attributes:
        branch_pos: Slot index along the branch axis (the lane).
        commit_pos: Slot index along the commit axis (the row).
    """

    branch_pos: int  # axis-bound: branch-axis (slot index)
    commit_pos: int  # axis-bound: commit-axis (slot index)


@dataclass(slots=True)
class LayoutGrid:
    """Integer-grid extent the layout commits to — slot counts only.

    The renderer transforms `(branch_pos, commit_pos)` slot indices to
    pixel coordinates using these counts together with the resolved
    theme's spacings and margins.

    Attributes:
        n_commits: Commit-axis slot count (pinned via `canvas.n_commits`
            or auto-fit from content extent). Needed by the coordinate
            transform because the bottom-to-top orientation places index
            0 at the largest y.
        n_branches: Branch-axis slot count.
    """

    n_commits: int  # axis-bound: commit-axis (slot count)
    n_branches: int  # axis-bound: branch-axis (slot count)


@dataclass(slots=True)
class LaneSegment:
    """One contiguous stretch of a branch's life spent on a single lane.

    A branch with a static lane has exactly one segment spanning its
    whole life; a branch that migrates lanes mid-life has one segment per
    lane it occupies, ordered along the commit axis and jointly covering
    `[branch.start, branch.end]`.

    Attributes:
        lane: Slot index along the branch axis for this stretch.
        start: Commit-axis position where this stretch begins (inclusive).
        end: Commit-axis position where this stretch ends (inclusive).
    """

    lane: int  # axis-bound: branch-axis (slot index)
    start: int  # axis-bound: commit-axis (slot index)
    end: int  # axis-bound: commit-axis (slot index)


@dataclass(slots=True)
class LayoutBranch:
    """One branch as the renderer should draw it.

    The branch's commit-axis span (`start` / `end`) and its starting lane
    (`start_lane`) are derived from `segments`, which is the single source
    of truth for where the branch sits on the grid.

    Attributes:
        id: Stable opaque branch id matching `BranchState.id`. The
            renderer uses this to look up per-branch presentational
            overrides (colour, label-side) on the resolved theme.
        name: Branch name (used to draw the name pill).
        segments: The lanes this branch occupies over its life, ordered
            along the commit axis and jointly covering its span. A
            static-lane branch has exactly one segment; a migrating
            branch has one per lane stretch.
        tip_commit_id: The commit this branch's ref points at — its tip
            (`commit_ids[-1]`) when it has commits, else its branch-off
            commit (`rooted_on_commit`), else None for a never-committed
            first branch. Lets the renderer place a branch's name pill at
            its ref target; a commit may be the ref target of several
            branches.
    """

    id: str
    name: str
    segments: list[LaneSegment]
    tip_commit_id: str | None

    @property
    def start(self) -> int:
        """Commit-axis position where the branch begins (its first segment's start)."""
        return self.segments[0].start

    @property
    def end(self) -> int:
        """Commit-axis position of the branch's newest end (its last segment's end)."""
        return self.segments[-1].end

    @property
    def start_lane(self) -> int:
        """Lane the branch occupies at its start row (its first segment's lane)."""
        return self.segments[0].lane

    def lane_at(self, row: int) -> int:
        """Return the lane this branch occupies at commit-axis `row`.

        Rows below the first segment clamp to the first segment's lane
        and rows above the last segment clamp to the last segment's lane,
        so callers can query projected positions just past the tip (e.g.
        a pull request's projected merge row).

        Args:
            row: Commit-axis slot index to resolve.

        Returns:
            The lane (branch-axis slot index) occupied at `row`.
        """
        for segment in self.segments:
            if row <= segment.end:
                return segment.lane
        return self.segments[-1].lane


@dataclass(slots=True)
class LayoutCommit:
    """One commit as the renderer should draw it.

    Attributes:
        id: The commit's id (matching `CommitState.id` in state).
        branch_id: Id of the branch the commit lives on; the renderer
            uses this to resolve per-branch presentational overrides
            (colour, label-side) on the resolved theme.
        branch_pos: Slot index along the branch axis.
        commit_pos: Slot index along the commit axis (0 = oldest).
        msg: Optional commit message — drawn as the primary label line.
        hash: Optional resolved hash string — drawn as the secondary
            label line. Already resolved from any `"auto"` sentinel.
        highlight: True when the commit should render with the highlight
            visual (enlarged dot + bold label).
        is_merge: True when the commit has two or more parents (a merge
            commit); selects the merge-commit dot style at render time.
    """

    id: str
    branch_id: str
    branch_pos: int  # axis-bound: branch-axis (slot index)
    commit_pos: int  # axis-bound: commit-axis (slot index)
    msg: str | None
    hash: str | None
    highlight: bool
    is_merge: bool


@dataclass(slots=True)
class LayoutArc:
    """One connector between a trunk point and a branch point on two lanes.

    Every connector spans a single commit row — the branch *lines* carry
    the long-distance travel. Used for branch-off connectors (trunk = the
    parent commit; branch = the new branch's start one row later), merge
    connectors (trunk = the merge commit; branch = the merged-in branch's
    line one row below the merge), and lane-change connectors (both ends
    on the migrating branch's own line). The renderer derives every
    presentational decision from the two points:

    - the **elbow** sits at `(branch_point lane, trunk_point row)`;
    - the **branch-off vs merge look** is `sign(branch_point.commit_pos
      − trunk_point.commit_pos)` — branch point above the trunk reads as
      a branch-off, below as a merge (they are mirror images across the
      commit axis);
    - **colour** is the branch passing through the branch point.

    Attributes:
        kind: What the connector represents (branch-off, merge, or
            lane-change). Carried explicitly because geometry alone
            cannot tell a lane-change apart from a branch-off / merge.
        trunk_point: Where the connector tees laterally into the ongoing
            branch (the lateral leg).
        branch_point: Where the connector aligns with a branch's own
            line — that branch's start or tip (the tangent leg).
    """

    kind: LayoutArcKind
    trunk_point: GridSlot
    branch_point: GridSlot


@dataclass(slots=True)
class LayoutPullRequest:
    """One open pull-request as the renderer should draw it.

    Geometrically the same shape as a merge connector — `trunk_point` is
    the projected merge point on the target lane, `branch_point` is the
    source tip — distinguished from a real merge by its dashed stroke and
    the optional title pill anchored at the source tip.

    Endpoints are recomputed every layout cycle from the branches'
    current tips, so as new commits land on either side the visual
    advances ("live-tracking").

    Attributes:
        id: The PR's id (matches `PullRequestState.id`).
        trunk_point: Projected merge point — the target branch's lane at
            the row a real `merge` would land at if it ran now.
        branch_point: The source tip (where the arc begins).
        title: Optional PR title; when None no pill is rendered.
    """

    id: str
    trunk_point: GridSlot
    branch_point: GridSlot
    title: str | None


@dataclass(slots=True)
class Layout:
    """Per-diagram layout: every grid-side decision the renderer needs.

    Attributes:
        grid: Integer-grid extent (slot counts).
        branches: One `LayoutBranch` per declared branch, in declaration
            order.
        commits: One `LayoutCommit` per surviving commit, keyed by id
            for renderer convenience.
        arcs: All connectors (branch-off + merge) in z-order
            (back-to-front).
        pull_requests: One `LayoutPullRequest` per open PR, in the
            order they were declared.
    """

    grid: LayoutGrid
    branches: list[LayoutBranch] = field(default_factory=list)
    commits: dict[str, LayoutCommit] = field(default_factory=dict)
    arcs: list[LayoutArc] = field(default_factory=list)
    pull_requests: list[LayoutPullRequest] = field(default_factory=list)
