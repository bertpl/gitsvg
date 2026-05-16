"""Layout engine — turn validated `State` into a render-ready `Layout`.

`compute_layout(state)` is a pure transformation. It walks state once,
producing a `Layout` with integer-grid positions, resolved label sides,
pre-computed arcs (branch-off + merge), pre-enumerated branch guides,
and the grid extent. The renderer consumes the result alongside a
resolved `Theme` to make every pixel-side decision.

The pipeline runs in three phases. Phase 1 walks every commit in
chronological order and computes its `commit_pos` together with each
branch's `start` and `end` — purely commit-axis values, with no
dependence on lane assignment. Phase 2 walks branches in declaration
order and picks each branch's lane: an explicit `branch_pos:` override
takes precedence; otherwise the lane-reuse heuristic walks `K+1, K+2,
…` and picks the first lane free of commits at positions `≥ L+1`,
where `(K, L)` is the parent commit's position. Phase 3 builds the
`Layout` dataclasses with both axes filled in.

Heuristic notes:

- **Branch axis (default).** First branch (no parent) gets lane 0.
  Subsequent branches reclaim the leftmost lane that is free at the new
  branch's first-commit row. Empty branches contribute a single
  pseudo-commit at their `start`; commits contribute their `commit_pos`.
  Branch lines, branch-off arcs, merge arcs, and pills do not block.
- **Branch axis (override).** When `BranchState.branch_pos` is set, the
  layout engine takes the value verbatim — no overlap check, no
  leftward-branching rejection. Same posture as `grid:` overrides.
- **Branch start (commit axis).** `start = parent_commit.commit_pos + 1`
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
  commit's position to the branch's start, tagged with the *target*
  (new) branch's id.
- **Merge arcs**: one per cross-lane parent on any commit with
  `len(parents) >= 2`, tagged with the *source* (parent) branch's id.
- **Branch guides**: one per occupied branch-axis lane.
- **Grid extent**: `n_commits` / `n_branches` honour pinned values on
  `state.grid` when set; otherwise auto-fit from the visible content
  (including any open pull-request's projected merge row).
"""

from gitsvg.file_format import LabelSide
from gitsvg.layout._layout import (
    Layout,
    LayoutArc,
    LayoutBranch,
    LayoutCommit,
    LayoutGrid,
    LayoutGuide,
    LayoutPullRequest,
)
from gitsvg.layout._occupancy import Occupancy
from gitsvg.state import State

_DEFAULT_LABEL_SIDE = (
    LabelSide.AFTER  # fallback when a `branch` op omits `label_side`; commits inherit their branch's resolved side
)


def compute_layout(state: State) -> Layout:
    """Compute a render-ready `Layout` from a fully-built `State`.

    Args:
        state: The state engine's output. Must be a clean validation
            (any errors would have been caught before this point); the
            layout engine does not re-validate.

    Returns:
        A `Layout` with positions, resolved label sides, pre-computed
        arcs and guides, and the grid extent.
    """
    # --- Phase 1: commit positions --------------
    chain_parent: dict[str, str | None] = _compute_chain_parents(state)
    commit_pos_by_id: dict[str, int] = {}
    branch_starts: dict[str, int] = {}
    branch_ends: dict[str, int] = {}

    for cid, cstate in state.commits.items():
        _ensure_branch_start(cstate.branch, state, commit_pos_by_id, branch_starts, branch_ends)
        commit_pos = _compute_commit_pos(cid, cstate, chain_parent, commit_pos_by_id, branch_starts)
        commit_pos_by_id[cid] = commit_pos
        branch_ends[cstate.branch] = max(branch_ends[cstate.branch], commit_pos)

    for name in state.branch_order:
        _ensure_branch_start(name, state, commit_pos_by_id, branch_starts, branch_ends)

    # --- Phase 2: branch lanes ------------------
    occupancy = Occupancy()
    branch_pos_by_name: dict[str, int] = _assign_branch_lanes(state, commit_pos_by_id, branch_starts, occupancy)

    # --- Resolve per-branch view fields ---------
    branch_label_side_by_name: dict[str, LabelSide] = {
        name: _resolve_label_side(state, name) for name in state.branch_order
    }

    # --- Phase 3: build layout dataclasses ------
    commit_layouts: dict[str, LayoutCommit] = {
        cid: LayoutCommit(
            id=cid,
            branch_id=state.branches[cstate.branch].id,
            branch_pos=branch_pos_by_name[cstate.branch],
            commit_pos=commit_pos_by_id[cid],
            msg=cstate.msg,
            hash=cstate.hash,
            highlight=cstate.highlight,
            label_side=branch_label_side_by_name[cstate.branch],
        )
        for cid, cstate in state.commits.items()
    }

    branches: list[LayoutBranch] = [
        LayoutBranch(
            id=state.branches[name].id,
            name=name,
            branch_pos=branch_pos_by_name[name],
            start=branch_starts[name],
            end=branch_ends[name],
            label_side=branch_label_side_by_name[name],
        )
        for name in state.branch_order
    ]

    # --- Build arc list -------------------------
    arcs: list[LayoutArc] = [
        *_branch_off_arcs(state, branches, commit_layouts),
        *_merge_arcs(state, commit_layouts),
    ]

    # --- Build guide list -----------------------
    guides = [LayoutGuide(branch_pos=lane) for lane in occupancy.occupied_lanes()]

    # --- Build pull-request list ----------------
    pull_requests = _build_pull_requests(state, branches)

    # --- Compute grid extent --------------------
    grid = _compute_grid(state, branches, commit_layouts, pull_requests)

    return Layout(
        grid=grid,
        branches=branches,
        commits=commit_layouts,
        arcs=arcs,
        guides=guides,
        pull_requests=pull_requests,
    )


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
    commit_pos_by_id: dict[str, int],
    branch_starts: dict[str, int],
    branch_ends: dict[str, int],
) -> None:
    """Compute and cache `branch_starts[branch_name]` if not yet known.

    Branch starts depend on the parent commit's `commit_pos`. The parent
    commit is added to state before this branch is declared, so by the
    time we hit any commit on this branch (or process empty branches at
    the end), the parent commit is already in `commit_pos_by_id`.
    """
    if branch_name in branch_starts:
        return
    branch_state = state.branches[branch_name]
    if branch_state.rooted_on_commit is None:
        start = 0
    else:
        parent_pos = commit_pos_by_id.get(branch_state.rooted_on_commit)
        # Defensive fallback for a dangling reference (would have been flagged
        # by end-of-file validation upstream).
        start = parent_pos + 1 if parent_pos is not None else 0
    branch_starts[branch_name] = start
    branch_ends[branch_name] = start


def _compute_commit_pos(
    commit_id: str,
    commit_state,
    chain_parent: dict[str, str | None],
    commit_pos_by_id: dict[str, int],
    branch_starts: dict[str, int],
) -> int:
    """Apply the uniform position rule: `max(effective_parents) + 1 + gap`.

    Effective parents = chain parent ∪ declared `parents:` list. When
    the set is empty (first commit on a root branch with no declared
    parents), the rule reduces to `branch.start + gap`.
    """
    effective_parent_positions: list[int] = []
    parent_id = chain_parent.get(commit_id)
    if parent_id is not None and parent_id in commit_pos_by_id:
        effective_parent_positions.append(commit_pos_by_id[parent_id])
    for declared in commit_state.parents:
        if declared in commit_pos_by_id:
            effective_parent_positions.append(commit_pos_by_id[declared])
    if effective_parent_positions:
        base = max(effective_parent_positions)
    else:
        base = branch_starts[commit_state.branch] - 1
    return base + 1 + commit_state.gap


# ==================================================================================================
#  Helpers — branch lane assignment
# ==================================================================================================
def _assign_branch_lanes(
    state: State,
    commit_pos_by_id: dict[str, int],
    branch_starts: dict[str, int],
    occupancy: Occupancy,
) -> dict[str, int]:
    """Assign every branch a branch-axis lane index.

    Walks `state.branch_order` and applies, per branch:

    1. If the branch's `branch_pos:` override is set, use it verbatim.
    2. Else if the branch has no parent (first declared branch), lane 0.
    3. Else run the lane-reuse heuristic: walk `K+1, K+2, …` from the
       parent commit's lane and pick the first lane where
       `occupancy.is_blocked_at_or_after(candidate, L+1)` is `False`,
       where `(K, L)` is the parent commit's `(branch_pos, commit_pos)`.

    Once a branch's lane is decided, the branch's points (its commits,
    or a pseudo-point at `start` for empty branches) are registered in
    `occupancy` so subsequent branches see the updated map.

    The override path is lenient — the supplied value is used even when
    `occupancy` would consider that lane blocked. Authors who set an
    override take responsibility for the layout. Override branches
    still register their points (the consult step is skipped, not the
    contribute step).

    **Forward references.** Declaration order can put a child branch
    before its parent — e.g. when the parent was removed and re-declared
    later (the rebase rebuild pattern). When the heuristic for X needs
    its parent branch's lane and that parent hasn't been processed yet,
    the parent is processed on demand (depth-first), so dependencies
    flow naturally regardless of `state.branch_order` position.

    Args:
        state: The validated state to lay out.
        commit_pos_by_id: Commit-axis positions computed in Phase 1.
        branch_starts: Branch-start commit-axis positions from Phase 1.
        occupancy: A fresh `Occupancy` to populate as branches are
            assigned. Read by subsequent layout steps (e.g. guide
            construction).

    Returns:
        Lane index (`branch_pos`) keyed by branch name.
    """
    positions: dict[str, int] = {}
    in_progress: set[str] = set()

    def assign(name: str) -> None:
        if name in positions or name in in_progress:
            return
        in_progress.add(name)
        branch = state.branches[name]
        if branch.branch_pos is not None:
            positions[name] = branch.branch_pos
        else:
            parent_lane, parent_pos = _resolve_parent_anchor(
                state, branch, positions, commit_pos_by_id, branch_starts, assign
            )
            if parent_lane is None:
                positions[name] = 0
            else:
                positions[name] = _pick_free_lane(
                    parent_lane=parent_lane,
                    threshold=parent_pos + 1,
                    occupancy=occupancy,
                )
        _register_branch_points(name, positions[name], state, commit_pos_by_id, branch_starts, occupancy)
        in_progress.discard(name)

    for name in state.branch_order:
        assign(name)

    return positions


def _register_branch_points(
    branch_name: str,
    branch_pos: int,
    state: State,
    commit_pos_by_id: dict[str, int],
    branch_starts: dict[str, int],
    occupancy: Occupancy,
) -> None:
    """Register `branch_name`'s occupancy footprint after its lane is decided.

    Every commit on the branch contributes a point at its
    `(branch_pos, commit_pos)`. An empty branch contributes a single
    pseudo-point at `(branch_pos, branch.start)` — preserves the
    long-standing rule that an empty branch still claims its lane at
    its start row.

    Args:
        branch_name: Name of the branch being registered.
        branch_pos: The lane index the branch was just assigned.
        state: Validated state (provides `branch.commit_ids`).
        commit_pos_by_id: Phase-1 commit-axis positions.
        branch_starts: Phase-1 branch starts.
        occupancy: The occupancy structure to write to.
    """
    branch_state = state.branches[branch_name]
    if branch_state.commit_ids:
        for cid in branch_state.commit_ids:
            row = commit_pos_by_id.get(cid)
            if row is not None:
                occupancy.add(branch_pos, row)
    else:
        occupancy.add(branch_pos, branch_starts[branch_name])


def _resolve_parent_anchor(
    state: State,
    branch,
    positions: dict[str, int],
    commit_pos_by_id: dict[str, int],
    branch_starts: dict[str, int],
    ensure_assigned,
) -> tuple[int | None, int]:
    """Resolve the parent (branch_pos, commit_pos) anchor for a new branch.

    Returns:
        `(parent_lane, parent_commit_pos)`. `parent_lane` is `None` for
        a root branch with no parent. When the parent branch exists but
        had no commits at the moment the new branch was declared,
        `parent_commit_pos` is `parent_branch.start - 1` so that
        `threshold = parent_commit_pos + 1` equals the parent branch's
        `start`, which is the row the new branch's first commit shares
        with the parent's pseudo-commit.

    Forward references through `state.branch_order` are resolved by
    invoking `ensure_assigned(parent_branch_name)` before reading
    `positions[parent_branch_name]`.
    """
    if branch.rooted_on_commit is not None and branch.rooted_on_commit in state.commits:
        parent_branch_name = state.commits[branch.rooted_on_commit].branch
        if parent_branch_name in state.branches:
            ensure_assigned(parent_branch_name)
            if parent_branch_name in positions:
                return positions[parent_branch_name], commit_pos_by_id[branch.rooted_on_commit]
    if branch.from_branch is not None and branch.from_branch in state.branches:
        ensure_assigned(branch.from_branch)
        if branch.from_branch in positions:
            return positions[branch.from_branch], branch_starts[branch.from_branch] - 1
    return None, 0


def _pick_free_lane(
    *,
    parent_lane: int,
    threshold: int,
    occupancy: Occupancy,
) -> int:
    """Walk `parent_lane + 1, +2, …` and return the first lane free at `threshold`.

    A lane is free iff `occupancy.is_blocked_at_or_after(candidate,
    threshold)` is `False` — i.e. no registered point on that lane
    sits at row `>= threshold`.
    """
    candidate = parent_lane + 1
    while occupancy.is_blocked_at_or_after(candidate, threshold):
        candidate += 1
    return candidate


# ==================================================================================================
#  Helpers — per-branch view fields
# ==================================================================================================
def _resolve_label_side(state: State, branch_name: str) -> LabelSide:
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
) -> list[LayoutArc]:
    """One branch-off arc per non-root branch, tagged with the target branch's id."""
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
                color_branch_id=branch_layout.id,
                vertical_first=False,
            )
        )
    return arcs


def _merge_arcs(
    state: State,
    commit_layouts: dict[str, LayoutCommit],
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
            from_branch_id = (
                state.branches[from_branch_name].id if from_branch_name in state.branches else commit_layout.branch_id
            )
            arcs.append(
                LayoutArc(
                    kind="merge",
                    from_branch_pos=parent_layout.branch_pos,
                    from_commit_pos=parent_layout.commit_pos,
                    to_branch_pos=commit_layout.branch_pos,
                    to_commit_pos=commit_layout.commit_pos,
                    color_branch_id=from_branch_id,
                    vertical_first=True,
                )
            )
    return arcs


# ==================================================================================================
#  Helpers — pull requests
# ==================================================================================================
def _build_pull_requests(state: State, branches: list[LayoutBranch]) -> list[LayoutPullRequest]:
    """Build one `LayoutPullRequest` per open PR in state.

    Endpoints are resolved from the current branch tips:

    - `from_commit_pos` is the source branch's `end` (latest commit
      row, or `start` for empty branches).
    - `to_commit_pos` is the projected merge-commit row on the target
      lane, computed with the same anchor formula a real `merge` would
      use: `max(from.end, into.end) + 1`.

    Branches that no longer exist in `branches` (a clean state should
    never produce this; defensive against partial-validation calls)
    cause the PR to be skipped silently.
    """
    branches_by_name = {b.name: b for b in branches}
    pull_requests: list[LayoutPullRequest] = []
    for pr_id, pr_state in state.pull_requests.items():
        from_branch = branches_by_name.get(pr_state.from_branch)
        into_branch = branches_by_name.get(pr_state.into_branch)
        if from_branch is None or into_branch is None:
            continue
        projected_merge_pos = max(from_branch.end, into_branch.end) + 1
        pull_requests.append(
            LayoutPullRequest(
                id=pr_id,
                from_branch_pos=from_branch.branch_pos,
                from_commit_pos=from_branch.end,
                to_branch_pos=into_branch.branch_pos,
                to_commit_pos=projected_merge_pos,
                color_branch_id=from_branch.id,
                title=pr_state.title,
            )
        )
    return pull_requests


# ==================================================================================================
#  Helpers — grid extent
# ==================================================================================================
def _compute_grid(
    state: State,
    branches: list[LayoutBranch],
    commit_layouts: dict[str, LayoutCommit],
    pull_requests: list[LayoutPullRequest],
) -> LayoutGrid:
    """Compute the integer-grid extent.

    Honours pinned `n_commits` / `n_branches` on `state.grid` when
    set; otherwise auto-fits to the visible content (commits, branch
    spans, and any open pull-request's projected merge row).
    """
    user_grid = state.grid

    max_branch_pos = max((b.branch_pos for b in branches), default=0)
    max_commit_pos_from_commits = max((c.commit_pos for c in commit_layouts.values()), default=-1)
    max_commit_pos_from_branches = max((b.end for b in branches), default=-1)
    max_commit_pos_from_prs = max((pr.to_commit_pos for pr in pull_requests), default=-1)
    max_commit_pos = max(max_commit_pos_from_commits, max_commit_pos_from_branches, max_commit_pos_from_prs)
    auto_n_commits = max_commit_pos + 1 if max_commit_pos >= 0 else 1
    auto_n_branches = max_branch_pos + 1 if branches else 1

    n_commits = _override(user_grid, "n_commits", auto_n_commits)
    n_branches = _override(user_grid, "n_branches", auto_n_branches)

    return LayoutGrid(n_commits=n_commits, n_branches=n_branches)


def _override(user_grid, attr: str, default):
    """Return the user's pinned value for `attr` if set, else the default."""
    if user_grid is None:
        return default
    pinned = getattr(user_grid, attr, None)
    return pinned if pinned is not None else default
