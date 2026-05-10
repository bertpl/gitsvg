"""Layout dataclasses — the complete render-ready intermediate representation.

Produced by `gitsvg.layout.compute_layout(state)` from a fully-built
`State`, consumed by `gitsvg.render.render(layout)`. Every field the
renderer needs is pre-resolved here:

- Resolved hex colours (no colour-cycle logic in the renderer).
- Resolved label sides (no `None`-fallback logic in the renderer).
- Resolved hash strings (auto-resolved 7-char hex from state, copied
  across).
- Pre-computed arc connectors (one entry per branch-off + merge arc).
- Pre-enumerated branch guides (one entry per occupied lane).
- Canvas dimensions.

Different layout strategies (the default declaration-order
sequential assignment, the lane-reuse strategy, future left-to-
right orientations) all produce the same `Layout` schema, so the
renderer stays oblivious.
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class LayoutCanvas:
    """Computed canvas dimensions and the effective spacing/margins the
    renderer's geometry transform reads from.

    Effective values come from the layout engine after merging the input's
    `canvas:` op overrides with auto-fit defaults. The renderer never has
    to look at constants — every value it needs to place a primitive is
    on this object.

    Attributes:
        width: SVG canvas width in pixels.
        height: SVG canvas height in pixels.
        n_commits: Effective commit-axis slot count (pinned via `canvas.n_commits`
            or auto-fit from content). Needed by the coordinate transform
            because the bottom-to-top orientation places index 0 at the
            largest y.
        n_branches: Effective branch-axis slot count.
        branch_spacing: Effective pixel distance between adjacent branch-axis slots.
        commit_spacing: Effective pixel distance between adjacent commit-axis slots.
        margin_branch_axis_lower: Effective branch-axis margin at the lower end (lane 0 side).
        margin_branch_axis_upper: Effective branch-axis margin at the upper end (highest-lane side).
        margin_commit_axis_lower: Effective commit-axis margin at the lower end (oldest-commit side).
        margin_commit_axis_upper: Effective commit-axis margin at the upper end (newest-commit side).
    """

    width: float
    height: float
    n_commits: int
    n_branches: int
    branch_spacing: float
    commit_spacing: float
    margin_branch_axis_lower: float
    margin_branch_axis_upper: float
    margin_commit_axis_lower: float
    margin_commit_axis_upper: float


@dataclass(slots=True)
class LayoutBranch:
    """One branch as the renderer should draw it.

    Attributes:
        name: Branch name (used to draw the name pill once labels land).
        branch_pos: Slot index along the branch axis (the lane).
        start: Commit-axis position where the branch begins (the
            branch-off point — for non-root branches this is one slot
            above the parent commit's `commit_pos`).
        end: Commit-axis position of the latest commit on this branch,
            or `start` when the branch has no commits yet.
        color: Resolved hex colour string (explicit branch.color
            override, or the resolved default-cycle entry).
        label_side: Resolved label side, `"left"` or `"right"` — never
            `None` in the layout.
    """

    name: str
    branch_pos: int
    start: int
    end: int
    color: str
    label_side: str


@dataclass(slots=True)
class LayoutCommit:
    """One commit as the renderer should draw it.

    Attributes:
        id: The commit's id (matching `CommitState.id` in state).
        branch_pos: Slot index along the branch axis.
        commit_pos: Slot index along the commit axis (0 = oldest).
        color: Resolved hex colour string (the colour of the commit's
            branch; commits always sit on their branch's lane).
        msg: Optional commit message — drawn as the primary label line.
        hash: Optional resolved hash string — drawn as the secondary
            label line. Already resolved from any `"auto"` sentinel.
        highlight: True when the commit should render with the highlight
            visual (enlarged dot + bold label).
        label_side: Resolved label side for this commit (inherited from
            its branch).
    """

    id: str
    branch_pos: int
    commit_pos: int
    color: str
    msg: str | None
    hash: str | None
    highlight: bool
    label_side: str


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
        color: Resolved hex colour string. Branch-off arcs take the
            *target* (new) branch's colour; merge arcs take the
            *source* (from) branch's colour.
        vertical_first: True for merge arcs (vertical segment → arc →
            horizontal segment); False for branch-off arcs (horizontal
            → arc → vertical).
    """

    kind: str
    from_branch_pos: int
    from_commit_pos: int
    to_branch_pos: int
    to_commit_pos: int
    color: str
    vertical_first: bool


@dataclass(slots=True)
class LayoutGuide:
    """A faint dashed vertical guide for one occupied lane.

    Attributes:
        branch_pos: Slot index along the branch axis where the guide is
            drawn.
    """

    branch_pos: int


@dataclass(slots=True)
class Layout:
    """Per-diagram layout: everything the renderer needs to draw the picture.

    Attributes:
        canvas: Canvas dimensions.
        branches: One `LayoutBranch` per declared branch, in declaration
            order.
        commits: One `LayoutCommit` per surviving commit, keyed by id
            for renderer convenience.
        arcs: All connectors (branch-off + merge) in z-order
            (back-to-front).
        guides: One per occupied branch-axis lane.
    """

    canvas: LayoutCanvas
    branches: list[LayoutBranch] = field(default_factory=list)
    commits: dict[str, LayoutCommit] = field(default_factory=dict)
    arcs: list[LayoutArc] = field(default_factory=list)
    guides: list[LayoutGuide] = field(default_factory=list)
