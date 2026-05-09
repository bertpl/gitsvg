"""Layout engine — turn validated `State` into a render-ready `Layout`.

`compute_layout(state)` is a pure transformation. It walks state once,
producing a `Layout` with positions, resolved colours, resolved label
sides, pre-computed arcs (branch-off + merge), pre-enumerated branch
guides, and canvas dimensions. The renderer consumes the result with no
need to peek back into state.

Heuristics for the v0.0.3 default strategy:

- **Branch axis**: monotonic declaration order. `branch_pos[name] =
  state.branch_order.index(name)`. Lane reuse heuristics are deferred
  to v0.0.4 (they would replace this strategy with a smarter one).
- **Branch start (commit axis)**: `start = parent_commit.commit_pos + 1`
  for non-root branches; `0` for the root branch.
- **Commit positions** follow a single uniform rule:
  `commit_pos = max(effective_parent.commit_pos) + 1 + gap`,
  where *effective parents* are the commit's chain parent (the previous
  commit on its branch in `branch.commit_ids` order) plus its declared
  `parents:` list (deduplicated). For commits with no effective parents
  (the first commit on a branch), the formula reduces to
  `start + gap`. Merge commits and squash commits fall out as special
  cases of this rule with no extra logic.
- **Branch line span**: from `start` to `max(commit_pos for commit in
  branch.commits)`, or just `start` for empty branches.
- **Branch-off arcs**: one per non-root branch, from the parent
  commit's position to the branch's start, in the *target* (new)
  branch's colour.
- **Merge arcs**: one per cross-lane parent on any commit with
  `len(parents) >= 2`, in the *source* (parent) branch's colour.
- **Branch guides**: one per occupied branch-axis lane.
"""

from gitsvg._visual_constants import (
    BRANCH_LABEL_FONT_SIZE,
    BRANCH_NAME_PILL_OFFSET,
    BRANCH_SPACING,
    COLORS,
    COMMIT_SPACING,
    DEFAULT_BRANCH_COLORS,
    LABEL_OFFSET,
    MARGIN_BRANCH_AXIS_LOWER,
    MARGIN_BRANCH_AXIS_UPPER,
    MARGIN_COMMIT_AXIS_LOWER,
    MARGIN_COMMIT_AXIS_UPPER,
)
from gitsvg.layout._layout import (
    Layout,
    LayoutArc,
    LayoutBranch,
    LayoutCanvas,
    LayoutCommit,
    LayoutGuide,
)
from gitsvg.layout._metrics import commit_label_width, pill_width
from gitsvg.state import State

_DEFAULT_LABEL_SIDE = "right"


def compute_layout(state: State) -> Layout:
    """Compute a render-ready `Layout` from a fully-built `State`.

    Args:
        state: The state engine's output. Must be a clean validation
            (any errors would have been caught before this point); the
            layout engine does not re-validate.

    Returns:
        A `Layout` with positions, resolved colours/label sides,
        pre-computed arcs and guides, and canvas dimensions.
    """
    # --- Per-branch bookkeeping ------------------
    branch_pos_by_name: dict[str, int] = {name: i for i, name in enumerate(state.branch_order)}
    chain_parent: dict[str, str | None] = _compute_chain_parents(state)

    # --- Resolve per-branch view fields ----------
    branch_color_by_name: dict[str, str] = {
        name: _resolve_branch_color(state, name, branch_pos_by_name[name]) for name in state.branch_order
    }
    branch_label_side_by_name: dict[str, str] = {name: _resolve_label_side(state, name) for name in state.branch_order}

    # --- Lay out commits in state-insertion order ------
    commit_layouts: dict[str, LayoutCommit] = {}
    branch_starts: dict[str, int] = {}
    branch_ends: dict[str, int] = {}
    for cid, cstate in state.commits.items():
        _ensure_branch_start(cstate.branch, state, commit_layouts, branch_starts, branch_ends)
        commit_pos = _compute_commit_pos(cid, cstate, chain_parent, commit_layouts, branch_starts)
        commit_layouts[cid] = LayoutCommit(
            id=cid,
            branch_pos=branch_pos_by_name[cstate.branch],
            commit_pos=commit_pos,
            color=branch_color_by_name[cstate.branch],
            msg=cstate.msg,
            hash=cstate.hash,
            highlight=cstate.highlight,
            label_side=branch_label_side_by_name[cstate.branch],
        )
        branch_ends[cstate.branch] = max(branch_ends[cstate.branch], commit_pos)

    # --- Lay out empty branches (no commits) -----
    for name in state.branch_order:
        _ensure_branch_start(name, state, commit_layouts, branch_starts, branch_ends)

    # --- Build LayoutBranch list -----------------
    branches: list[LayoutBranch] = [
        LayoutBranch(
            name=name,
            branch_pos=branch_pos_by_name[name],
            start=branch_starts[name],
            end=branch_ends[name],
            color=branch_color_by_name[name],
            label_side=branch_label_side_by_name[name],
        )
        for name in state.branch_order
    ]

    # --- Build arc list --------------------------
    arcs: list[LayoutArc] = [
        *_branch_off_arcs(state, branches, commit_layouts, branch_color_by_name, branch_pos_by_name),
        *_merge_arcs(state, commit_layouts, branch_color_by_name),
    ]

    # --- Build guide list ------------------------
    occupied_lanes = sorted({b.branch_pos for b in branches})
    guides = [LayoutGuide(branch_pos=p) for p in occupied_lanes]

    # --- Compute canvas spec ---------------------
    canvas = _compute_canvas(state, branches, commit_layouts)

    return Layout(canvas=canvas, branches=branches, commits=commit_layouts, arcs=arcs, guides=guides)


# ==================================================================================================
#  Helpers — bookkeeping
# ==================================================================================================
def _compute_chain_parents(state: State) -> dict[str, str | None]:
    """Build a map of `commit_id → chain parent id` from `branch.commit_ids` order."""
    chain_parent: dict[str, str | None] = {}
    for branch_state in state.branches.values():
        previous: str | None = None
        for cid in branch_state.commit_ids:
            chain_parent[cid] = previous
            previous = cid
    return chain_parent


def _ensure_branch_start(
    branch_name: str,
    state: State,
    commit_layouts: dict[str, LayoutCommit],
    branch_starts: dict[str, int],
    branch_ends: dict[str, int],
) -> None:
    """Compute and cache `branch_starts[branch_name]` if not yet known.

    Branch starts depend on the parent commit's `commit_pos`. The parent
    commit is added to state before this branch is declared, so by the
    time we hit any commit on this branch (or process empty branches at
    the end), the parent commit is already in `commit_layouts`.
    """
    if branch_name in branch_starts:
        return
    branch_state = state.branches[branch_name]
    if branch_state.rooted_on_commit is None:
        start = 0
    else:
        parent_layout = commit_layouts.get(branch_state.rooted_on_commit)
        # Defensive fallback for a dangling reference (would have been flagged
        # by end-of-file validation upstream).
        start = parent_layout.commit_pos + 1 if parent_layout is not None else 0
    branch_starts[branch_name] = start
    branch_ends[branch_name] = start


def _compute_commit_pos(
    commit_id: str,
    commit_state,
    chain_parent: dict[str, str | None],
    commit_layouts: dict[str, LayoutCommit],
    branch_starts: dict[str, int],
) -> int:
    """Apply the uniform position rule: `max(effective_parents) + 1 + gap`.

    Effective parents = chain parent ∪ declared `parents:` list. When
    the set is empty (first commit on a root branch with no declared
    parents), the rule reduces to `branch.start + gap`.
    """
    effective_parent_positions: list[int] = []
    parent_id = chain_parent.get(commit_id)
    if parent_id is not None and parent_id in commit_layouts:
        effective_parent_positions.append(commit_layouts[parent_id].commit_pos)
    for declared in commit_state.parents:
        layout_for_declared = commit_layouts.get(declared)
        if layout_for_declared is not None:
            effective_parent_positions.append(layout_for_declared.commit_pos)
    if effective_parent_positions:
        base = max(effective_parent_positions)
    else:
        base = branch_starts[commit_state.branch] - 1
    return base + 1 + commit_state.gap


# ==================================================================================================
#  Helpers — per-branch view fields
# ==================================================================================================
def _resolve_branch_color(state: State, branch_name: str, declaration_index: int) -> str:
    """Pick the hex colour for a branch — explicit override else cycled default."""
    branch = state.branches[branch_name]
    if branch.color is not None:
        return branch.color
    if declaration_index == 0:
        return COLORS["main"]
    cycle_index = (declaration_index - 1) % len(DEFAULT_BRANCH_COLORS)
    return COLORS[DEFAULT_BRANCH_COLORS[cycle_index]]


def _resolve_label_side(state: State, branch_name: str) -> str:
    """Pick the label side for a branch — explicit override else the default."""
    branch = state.branches[branch_name]
    return branch.label_side or _DEFAULT_LABEL_SIDE


# ==================================================================================================
#  Helpers — arcs
# ==================================================================================================
def _branch_off_arcs(
    state: State,
    branches: list[LayoutBranch],
    commit_layouts: dict[str, LayoutCommit],
    branch_color_by_name: dict[str, str],
    branch_pos_by_name: dict[str, int],
) -> list[LayoutArc]:
    """One branch-off arc per non-root branch, in the target branch's colour."""
    arcs: list[LayoutArc] = []
    branch_layouts_by_name = {b.name: b for b in branches}
    for name in state.branch_order:
        branch_state = state.branches.get(name)
        if branch_state is None or branch_state.rooted_on_commit is None:
            continue
        parent_layout = commit_layouts.get(branch_state.rooted_on_commit)
        if parent_layout is None:
            continue
        branch_layout = branch_layouts_by_name[name]
        arcs.append(
            LayoutArc(
                kind="branch_off",
                from_branch_pos=parent_layout.branch_pos,
                from_commit_pos=parent_layout.commit_pos,
                to_branch_pos=branch_layout.branch_pos,
                to_commit_pos=branch_layout.start,
                color=branch_color_by_name[name],
                vertical_first=False,
            )
        )
    return arcs


def _merge_arcs(
    state: State,
    commit_layouts: dict[str, LayoutCommit],
    branch_color_by_name: dict[str, str],
) -> list[LayoutArc]:
    """One merge arc per parent on a different lane than its child commit."""
    arcs: list[LayoutArc] = []
    for cid, cstate in state.commits.items():
        commit_layout = commit_layouts.get(cid)
        if commit_layout is None or len(cstate.parents) < 2:
            continue
        for parent_id in cstate.parents:
            parent_layout = commit_layouts.get(parent_id)
            if parent_layout is None or parent_layout.branch_pos == commit_layout.branch_pos:
                continue
            parent_state = state.commits.get(parent_id)
            from_branch_name = parent_state.branch if parent_state is not None else cstate.branch
            from_color = branch_color_by_name.get(from_branch_name, commit_layout.color)
            arcs.append(
                LayoutArc(
                    kind="merge",
                    from_branch_pos=parent_layout.branch_pos,
                    from_commit_pos=parent_layout.commit_pos,
                    to_branch_pos=commit_layout.branch_pos,
                    to_commit_pos=commit_layout.commit_pos,
                    color=from_color,
                    vertical_first=True,
                )
            )
    return arcs


# ==================================================================================================
#  Helpers — canvas
# ==================================================================================================
def _compute_canvas(
    state: State,
    branches: list[LayoutBranch],
    commit_layouts: dict[str, LayoutCommit],
) -> LayoutCanvas:
    """Compute the effective canvas spec.

    Honours every `canvas:` op field that's set; falls back to auto-fit
    defaults for fields that aren't pinned. Auto-fit keeps the canvas
    just big enough to contain the longest visible labels and the
    branch-name pills.

    When `n_commits` / `n_branches` are pinned smaller than the actual
    content extent, the pinned values win — content past the pinned
    bounds is clipped by SVG's default overflow behaviour at render
    time.
    """
    user_canvas = state.canvas

    # Effective spacing — pinned wins, otherwise default constants.
    branch_spacing = _override(user_canvas, "branch_spacing", BRANCH_SPACING)
    commit_spacing = _override(user_canvas, "commit_spacing", COMMIT_SPACING)

    # Effective slot counts — pinned wins, otherwise auto-fit from extent.
    max_branch_pos = max((b.branch_pos for b in branches), default=0)
    max_commit_pos_from_commits = max((c.commit_pos for c in commit_layouts.values()), default=-1)
    max_commit_pos_from_branches = max((b.end for b in branches), default=-1)
    max_commit_pos = max(max_commit_pos_from_commits, max_commit_pos_from_branches)
    auto_n_commits = max_commit_pos + 1 if max_commit_pos >= 0 else 1
    auto_n_branches = max_branch_pos + 1 if branches else 1
    n_commits = _override(user_canvas, "n_commits", auto_n_commits)
    n_branches = _override(user_canvas, "n_branches", auto_n_branches)

    # Effective margins — pinned wins, otherwise auto-fit each side.
    margin_branch_axis_lower = _override(
        user_canvas,
        "margin_branch_axis_lower",
        _auto_fit_margin_branch_axis(branches, commit_layouts, branch_pos_filter=0, side="left"),
    )
    margin_branch_axis_upper = _override(
        user_canvas,
        "margin_branch_axis_upper",
        _auto_fit_margin_branch_axis(branches, commit_layouts, branch_pos_filter=max_branch_pos, side="right"),
    )
    margin_commit_axis_lower = _override(
        user_canvas,
        "margin_commit_axis_lower",
        _auto_fit_margin_commit_axis_lower(branches),
    )
    margin_commit_axis_upper = _override(user_canvas, "margin_commit_axis_upper", float(MARGIN_COMMIT_AXIS_UPPER))

    width = margin_branch_axis_lower + (n_branches - 1) * branch_spacing + margin_branch_axis_upper
    height = margin_commit_axis_upper + (n_commits - 1) * commit_spacing + margin_commit_axis_lower
    return LayoutCanvas(
        width=width,
        height=height,
        n_commits=n_commits,
        n_branches=n_branches,
        branch_spacing=branch_spacing,
        commit_spacing=commit_spacing,
        margin_branch_axis_lower=margin_branch_axis_lower,
        margin_branch_axis_upper=margin_branch_axis_upper,
        margin_commit_axis_lower=margin_commit_axis_lower,
        margin_commit_axis_upper=margin_commit_axis_upper,
    )


def _override(user_canvas, attr: str, default):
    """Return the user's pinned value for `attr` if set, else the default."""
    if user_canvas is None:
        return default
    pinned = getattr(user_canvas, attr, None)
    return pinned if pinned is not None else default


def _auto_fit_margin_branch_axis(
    branches: list[LayoutBranch],
    commit_layouts: dict[str, LayoutCommit],
    *,
    branch_pos_filter: int,
    side: str,
) -> float:
    """Compute the auto-fit margin for one branch-axis end (left or right).

    Considers the half-pill-width of any pill on the edge lane plus the
    width of any commit label whose `label_side` points outward from
    that lane.
    """
    if side == "left":
        default = MARGIN_BRANCH_AXIS_LOWER
        outward_label_side = "left"
    else:
        default = MARGIN_BRANCH_AXIS_UPPER
        outward_label_side = "right"

    needed: float = 0.0
    pad = 4.0
    for branch in branches:
        if branch.branch_pos == branch_pos_filter:
            needed = max(needed, pill_width(branch.name) / 2 + pad)
    for commit in commit_layouts.values():
        if commit.branch_pos == branch_pos_filter and commit.label_side == outward_label_side:
            needed = max(needed, LABEL_OFFSET + commit_label_width(commit) + pad)
    return max(default, needed)


def _auto_fit_margin_commit_axis_lower(branches: list[LayoutBranch]) -> float:
    """Compute the auto-fit lower margin on the commit axis.

    The pill of any branch with `start = min(start)` sits closest to the
    canvas bottom. Reserve enough room for it: `BRANCH_NAME_PILL_OFFSET`
    (centre offset) + half the pill height + a small pad.
    """
    if not branches:
        return float(MARGIN_COMMIT_AXIS_LOWER)
    pill_height = BRANCH_LABEL_FONT_SIZE + 8  # matches `_branch_pill._PILL_PADDING_Y`
    pill_room = BRANCH_NAME_PILL_OFFSET + pill_height / 2 + 4.0
    return max(float(MARGIN_COMMIT_AXIS_LOWER), pill_room)
