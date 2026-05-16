"""Layout dataclasses — the integer-grid intermediate representation.

Produced by `gitsvg.layout.compute_layout(state)` from a fully-built
`State`, consumed by `gitsvg.render.render(layout, theme)`. The
layout is *exclusively* about integer-grid positioning:

- `branch_pos` / `commit_pos` slot indices for every entity.
- Semantic identifiers (branch `id`, commit `id`, PR `id`).
- Resolved label sides (no `None`-fallback logic in the renderer).
- Resolved hash strings (auto-resolved 7-char hex from state).
- Pre-computed arc connectors and branch guides as slot pairs.
- Grid extent (`n_commits`, `n_branches`).

Layout output carries **no** colour, pixel, font, stroke, or
opacity data. Every presentational decision happens in the renderer
from the resolved `Theme`.

Different layout strategies (default declaration-order assignment,
lane-reuse, future left-to-right orientations) all produce the same
`Layout` schema, so the renderer stays oblivious.
"""

from dataclasses import dataclass, field

from gitsvg.file_format import LabelSide


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
class LayoutBranch:
    """One branch as the renderer should draw it.

    Attributes:
        id: Stable opaque branch id matching `BranchState.id`. The
            renderer uses this to look up per-branch presentational
            overrides (e.g. colour) on the resolved theme.
        name: Branch name (used to draw the name pill).
        branch_pos: Slot index along the branch axis (the lane).
        start: Commit-axis position where the branch begins (the
            branch-off point — for non-root branches this is one slot
            above the parent commit's `commit_pos`).
        end: Commit-axis position of the latest commit on this branch,
            or `start` when the branch has no commits yet.
        label_side: Resolved branch-axis-index side for the branch's
            commit labels: `"before"` = lower-index side; `"after"` =
            higher-index side. Orientation-invariant — the renderer
            maps to a pixel side per `theme.orientation`. Never `None`
            in the layout: the layout engine fills in the default when
            the branch op omits it.
    """

    id: str
    name: str
    branch_pos: int  # axis-bound: branch-axis (slot index)
    start: int  # axis-bound: commit-axis (slot index)
    end: int  # axis-bound: commit-axis (slot index)
    label_side: LabelSide  # axis-bound: branch-axis (axis-index side: BEFORE = lower index, AFTER = higher index)


@dataclass(slots=True)
class LayoutCommit:
    """One commit as the renderer should draw it.

    Attributes:
        id: The commit's id (matching `CommitState.id` in state).
        branch_id: Id of the branch the commit lives on; the renderer
            uses this to resolve the commit's colour.
        branch_pos: Slot index along the branch axis.
        commit_pos: Slot index along the commit axis (0 = oldest).
        msg: Optional commit message — drawn as the primary label line.
        hash: Optional resolved hash string — drawn as the secondary
            label line. Already resolved from any `"auto"` sentinel.
        highlight: True when the commit should render with the highlight
            visual (enlarged dot + bold label).
        label_side: Resolved branch-axis-index side for this commit's
            label: `"before"` = lower-index side; `"after"` =
            higher-index side. Inherited from the commit's branch.
            Orientation-invariant — the renderer maps to a pixel side
            per `theme.orientation`.
    """

    id: str
    branch_id: str
    branch_pos: int  # axis-bound: branch-axis (slot index)
    commit_pos: int  # axis-bound: commit-axis (slot index)
    msg: str | None
    hash: str | None
    highlight: bool
    label_side: LabelSide  # axis-bound: branch-axis (axis-index side: BEFORE = lower index, AFTER = higher index)


@dataclass(slots=True)
class LayoutArc:
    """One curved connector between two points on different lanes.

    Used for branch-off arcs (a parent commit on one lane → the start
    of a child branch on another lane) and merge arcs (the from-branch
    tip → the merge commit on the into-branch's lane).

    Attributes:
        kind: Either `"branch_off"` or `"merge"`.
        from_branch_pos: Source point's branch-axis index.
        from_commit_pos: Source point's commit-axis index.
        to_branch_pos: Target point's branch-axis index.
        to_commit_pos: Target point's commit-axis index.
        color_branch_id: Id of the branch whose colour this arc takes.
            Branch-off arcs use the *target* (new) branch; merge arcs
            use the *source* (from) branch. The renderer resolves the
            actual hex value via the theme.
        vertical_first: True for merge arcs (vertical segment → arc →
            horizontal segment); False for branch-off arcs (horizontal
            → arc → vertical).
    """

    kind: str
    from_branch_pos: int  # axis-bound: branch-axis (slot index)
    from_commit_pos: int  # axis-bound: commit-axis (slot index)
    to_branch_pos: int  # axis-bound: branch-axis (slot index)
    to_commit_pos: int  # axis-bound: commit-axis (slot index)
    color_branch_id: str
    vertical_first: bool


@dataclass(slots=True)
class LayoutGuide:
    """A faint dashed vertical guide for one occupied lane.

    Attributes:
        branch_pos: Slot index along the branch axis where the guide is
            drawn.
    """

    branch_pos: int  # axis-bound: branch-axis (slot index)


@dataclass(slots=True)
class LayoutPullRequest:
    """One open pull-request as the renderer should draw it.

    Geometrically the same shape as a merge arc-and-line: a vertical
    segment up from the source tip → a quarter arc → a horizontal
    segment along the target lane to the projected merge point.
    Distinguished from a real merge by its dashed stroke and the
    optional title pill anchored at the source tip.

    Endpoints are recomputed every layout cycle from the branches'
    current tips, so as new commits land on either side the visual
    advances ("live-tracking").

    Attributes:
        id: The PR's id (matches `PullRequestState.id`).
        from_branch_pos: Source branch's lane (where the arc begins).
        from_commit_pos: Source-tip row (where the arc begins).
        to_branch_pos: Target branch's lane (where the horizontal
            segment runs).
        to_commit_pos: Projected merge-commit row on the target lane —
            the position a real `merge` would land at if it ran now.
        color_branch_id: Id of the source branch — its colour drives the
            dashed arc and the title pill.
        title: Optional PR title; when None no pill is rendered.
    """

    id: str
    from_branch_pos: int  # axis-bound: branch-axis (slot index)
    from_commit_pos: int  # axis-bound: commit-axis (slot index)
    to_branch_pos: int  # axis-bound: branch-axis (slot index)
    to_commit_pos: int  # axis-bound: commit-axis (slot index)
    color_branch_id: str
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
        guides: One per occupied branch-axis lane.
        pull_requests: One `LayoutPullRequest` per open PR, in the
            order they were declared.
    """

    grid: LayoutGrid
    branches: list[LayoutBranch] = field(default_factory=list)
    commits: dict[str, LayoutCommit] = field(default_factory=dict)
    arcs: list[LayoutArc] = field(default_factory=list)
    guides: list[LayoutGuide] = field(default_factory=list)
    pull_requests: list[LayoutPullRequest] = field(default_factory=list)
