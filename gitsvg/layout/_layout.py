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

Every field carries a `Classification:` line in its per-field
docstring, enforced by the meta-test in `tests/architecture/`. See
`docs/architecture.md` invariant #2 for the taxonomy.
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class LayoutGrid:
    """Integer-grid extent the layout commits to — slot counts only.

    The renderer transforms `(branch_pos, commit_pos)` slot indices to
    pixel coordinates using these counts together with the resolved
    theme's spacings and margins.
    """

    n_commits: int
    """Commit-axis slot count (pinned via `canvas.n_commits` or auto-fit from content extent). Needed by the coordinate transform because the bottom-to-top orientation places index 0 at the largest y. Classification: axis-bound: commit-axis (slot count)."""

    n_branches: int
    """Branch-axis slot count. Classification: axis-bound: branch-axis (slot count)."""


@dataclass(slots=True)
class LayoutBranch:
    """One branch as the renderer should draw it."""

    id: str
    """Stable opaque branch id matching `BranchState.id`. The renderer uses this to look up per-branch presentational overrides (e.g. colour) on the resolved theme. Classification: not-applicable."""

    name: str
    """Branch name (used to draw the name pill). Classification: not-applicable."""

    branch_pos: int
    """Slot index along the branch axis (the lane). Classification: axis-bound: branch-axis (slot index)."""

    start: int
    """Commit-axis position where the branch begins (the branch-off point — for non-root branches this is one slot above the parent commit's `commit_pos`). Classification: axis-bound: commit-axis (slot index)."""

    end: int
    """Commit-axis position of the latest commit on this branch, or `start` when the branch has no commits yet. Classification: axis-bound: commit-axis (slot index)."""

    label_side: str
    """Resolved label side, `"left"` or `"right"` — never `None` in the layout. Picks which branch-axis side the commit-label stack is anchored to. Classification: direction-bound: branch-axis, set by side hint."""


@dataclass(slots=True)
class LayoutCommit:
    """One commit as the renderer should draw it."""

    id: str
    """The commit's id (matching `CommitState.id` in state). Classification: not-applicable."""

    branch_id: str
    """Id of the branch the commit lives on; the renderer uses this to resolve the commit's colour. Classification: not-applicable."""

    branch_pos: int
    """Slot index along the branch axis. Classification: axis-bound: branch-axis (slot index)."""

    commit_pos: int
    """Slot index along the commit axis (0 = oldest). Classification: axis-bound: commit-axis (slot index)."""

    msg: str | None
    """Optional commit message — drawn as the primary label line. Classification: not-applicable."""

    hash: str | None
    """Optional resolved hash string — drawn as the secondary label line. Already resolved from any `"auto"` sentinel. Classification: not-applicable."""

    highlight: bool
    """True when the commit should render with the highlight visual (enlarged dot + bold label). Classification: not-applicable."""

    label_side: str
    """Resolved label side for this commit (inherited from its branch). Classification: direction-bound: branch-axis, set by side hint."""


@dataclass(slots=True)
class LayoutArc:
    """One curved connector between two points on different lanes.

    Used for branch-off arcs (a parent commit on one lane → the start
    of a child branch on another lane) and merge arcs (the from-branch
    tip → the merge commit on the into-branch's lane).
    """

    kind: str
    """Either `"branch_off"` or `"merge"`. Classification: not-applicable."""

    from_branch_pos: int
    """Source point's branch-axis index. Classification: axis-bound: branch-axis (slot index)."""

    from_commit_pos: int
    """Source point's commit-axis index. Classification: axis-bound: commit-axis (slot index)."""

    to_branch_pos: int
    """Target point's branch-axis index. Classification: axis-bound: branch-axis (slot index)."""

    to_commit_pos: int
    """Target point's commit-axis index. Classification: axis-bound: commit-axis (slot index)."""

    color_branch_id: str
    """Id of the branch whose colour this arc takes. Branch-off arcs use the *target* (new) branch; merge arcs use the *source* (from) branch. The renderer resolves the actual hex value via the theme. Classification: not-applicable."""

    vertical_first: bool
    """True for merge arcs (vertical segment → arc → horizontal segment); False for branch-off arcs (horizontal → arc → vertical). Classification: not-applicable."""


@dataclass(slots=True)
class LayoutGuide:
    """A faint dashed vertical guide for one occupied lane."""

    branch_pos: int
    """Slot index along the branch axis where the guide is drawn. Classification: axis-bound: branch-axis (slot index)."""


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
    """

    id: str
    """The PR's id (matches `PullRequestState.id`). Classification: not-applicable."""

    from_branch_pos: int
    """Source branch's lane (where the arc begins). Classification: axis-bound: branch-axis (slot index)."""

    from_commit_pos: int
    """Source-tip row (where the arc begins). Classification: axis-bound: commit-axis (slot index)."""

    to_branch_pos: int
    """Target branch's lane (where the horizontal segment runs). Classification: axis-bound: branch-axis (slot index)."""

    to_commit_pos: int
    """Projected merge-commit row on the target lane — the position a real `merge` would land at if it ran now. Classification: axis-bound: commit-axis (slot index)."""

    color_branch_id: str
    """Id of the source branch — its colour drives the dashed arc and the title pill. Classification: not-applicable."""

    title: str | None
    """Optional PR title; when None no pill is rendered. Classification: not-applicable."""


@dataclass(slots=True)
class Layout:
    """Per-diagram layout: every grid-side decision the renderer needs."""

    canvas: LayoutGrid
    """Integer-grid extent (slot counts). Classification: not-applicable."""

    branches: list[LayoutBranch] = field(default_factory=list)
    """One `LayoutBranch` per declared branch, in declaration order. Classification: not-applicable."""

    commits: dict[str, LayoutCommit] = field(default_factory=dict)
    """One `LayoutCommit` per surviving commit, keyed by id for renderer convenience. Classification: not-applicable."""

    arcs: list[LayoutArc] = field(default_factory=list)
    """All connectors (branch-off + merge) in z-order (back-to-front). Classification: not-applicable."""

    guides: list[LayoutGuide] = field(default_factory=list)
    """One per occupied branch-axis lane. Classification: not-applicable."""

    pull_requests: list[LayoutPullRequest] = field(default_factory=list)
    """One `LayoutPullRequest` per open PR, in the order they were declared. Classification: not-applicable."""
