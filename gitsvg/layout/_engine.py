"""Layout engine — turn validated `State` into a render-ready `Layout`.

`compute_layout(state)` is a pure transformation. It walks state once,
producing a `Layout` with integer-grid positions, pre-computed arcs
(branch-off + merge), and the grid extent. The renderer consumes the
result alongside a resolved `Theme` to make every pixel-side decision.

The pipeline runs in three phases. Phase 1 walks every commit in
chronological order and computes its `commit_pos` together with each
branch's `start` and `end` — purely commit-axis values, with no
dependence on lane assignment. Phase 2 walks branches in declaration
order and picks each branch's lane: an explicit `branch_pos:` override
takes precedence; otherwise the lane-reuse heuristic walks `K+1, K+2,
…` and picks the first lane free of commits at positions `≥ L+1`,
where `(K, L)` is the parent commit's position. Each branch becomes a
single lane segment spanning its whole life. Under
`auto_lane_change` Phase 2 instead runs an event-sweep
(`_assign_lane_segments`) that packs the live branches into the lowest
lanes at every row, so a branch migrates downward as lower lanes free up
— yielding multiple lane segments per branch and a lane-change connector
at each transition. Phase 3 builds the `Layout` dataclasses with both
axes filled in.

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
- **Branch line span**: from `start` to the branch's `line_end` — its
  last commit, extended to one row below any merge / pull request it
  feeds (see `_line_ends`). Empty branches span just `start`.
- **Connectors are single-row hops.** Every connector spans one commit
  row; the branch *line* carries all the long-distance vertical travel.
  - **Branch-off arcs**: one per non-root branch — parent commit (trunk)
    → the branch's start one row later (branch point).
  - **Merge arcs**: one per merged-in parent on a commit with
    `len(parents) >= 2` — the merge commit (trunk) → the source branch's
    line at `merge_row - 1` (branch point).
- **Grid extent**: `n_commits` / `n_branches` honour pinned values on
  `state.grid` when set; otherwise auto-fit from the visible content
  (including any open pull-request's projected merge row).
"""

from collections.abc import Iterator

from gitsvg.layout._layout import (
    GridSlot,
    LaneSegment,
    Layout,
    LayoutArc,
    LayoutBranch,
    LayoutCommit,
    LayoutGrid,
    LayoutPullRequest,
)
from gitsvg.layout._layout_arc_kind import LayoutArcKind
from gitsvg.layout._layout_settings import LayoutSettings
from gitsvg.layout._occupancy import Occupancy
from gitsvg.state import State
from gitsvg.theme._commit_row_mode import CommitRowMode


def compute_layout(state: State, layout_settings: LayoutSettings | None = None) -> Layout:
    """Compute a render-ready `Layout` from a fully-built `State`.

    Args:
        state: The state engine's output. Must be a clean validation
            (any errors would have been caught before this point); the
            layout engine does not re-validate.
        layout_settings: The layout stage's slice of the resolved theme,
            produced by `Theme.split()`. Defaults to `LayoutSettings()`
            (every layout-policy field at its default) when omitted, so
            callers without a resolved theme — and tests — can compute a
            layout from `state` alone.

    Returns:
        A `Layout` with positions, pre-computed arcs, and the grid
        extent.
    """
    if layout_settings is None:
        layout_settings = LayoutSettings()
    # --- Phase 1: commit positions --------------
    chain_parent: dict[str, str | None] = _compute_chain_parents(state)
    commit_pos_by_id: dict[str, int] = {}
    branch_starts: dict[str, int] = {}
    branch_ends: dict[str, int] = {}

    # In `unique` mode every commit claims its own row, assigned in
    # declaration order: `next_row` tracks the lowest unclaimed row, so a
    # commit lands at `max(its shared row, next_row + gap)` — still below
    # its parents, but never sharing a row with another branch's commit.
    unique_rows = layout_settings.commit_row_mode is CommitRowMode.UNIQUE
    next_row = 0

    for cid, cstate in state.commits.items():
        _ensure_branch_start(cstate.branch, state, commit_pos_by_id, branch_starts, branch_ends)
        commit_pos = _compute_commit_pos(cid, cstate, chain_parent, commit_pos_by_id, branch_starts)
        if unique_rows:
            commit_pos = max(commit_pos, next_row + cstate.gap)
            next_row = commit_pos + 1
        commit_pos_by_id[cid] = commit_pos
        branch_ends[cstate.branch] = max(branch_ends[cstate.branch], commit_pos)

    for name in state.branch_order:
        _ensure_branch_start(name, state, commit_pos_by_id, branch_starts, branch_ends)

    # --- Phase 2: line / occupancy extents & lanes ----------
    # `line_end` is how far a branch's line is *drawn* — its last commit,
    # extended to one row below any merge / PR it feeds (those connectors
    # are single-row hops, so the line carries the vertical travel).
    # `occ_end` is how far the lane is *reserved*: `merge_lane_clearance`
    # rows further for a merged / PR'd source (default one), because the
    # connector climbs the source lane through the merge row, so a sibling
    # may only reclaim the lane afterwards.
    line_ends, occ_ends = _branch_extents(state, commit_pos_by_id, branch_ends, layout_settings.merge_lane_clearance)
    if layout_settings.auto_lane_change:
        segments_by_name = _assign_lane_segments(state, branch_starts, line_ends, occ_ends)
    else:
        occupancy = Occupancy()
        branch_pos_by_name = _assign_branch_lanes(state, commit_pos_by_id, branch_starts, occupancy)
        segments_by_name = {
            name: [LaneSegment(lane=branch_pos_by_name[name], start=branch_starts[name], end=line_ends[name])]
            for name in state.branch_order
        }

    # --- Phase 3: build layout dataclasses ------
    # Branches first, so each commit can resolve its lane from the
    # segment covering its row (`lane_at`) — the migrating-branch case.
    branches: list[LayoutBranch] = [
        LayoutBranch(id=state.branches[name].id, name=name, segments=segments_by_name[name])
        for name in state.branch_order
    ]
    branch_by_name: dict[str, LayoutBranch] = {b.name: b for b in branches}

    commit_layouts: dict[str, LayoutCommit] = {
        cid: LayoutCommit(
            id=cid,
            branch_id=state.branches[cstate.branch].id,
            branch_pos=branch_by_name[cstate.branch].lane_at(commit_pos_by_id[cid]),
            commit_pos=commit_pos_by_id[cid],
            msg=cstate.msg,
            hash=cstate.hash,
            highlight=cstate.highlight,
            is_merge=len(cstate.parents) >= 2,
        )
        for cid, cstate in state.commits.items()
    }

    # --- Build arc list -------------------------
    arcs: list[LayoutArc] = [
        *_branch_off_arcs(state, branches, commit_layouts),
        *_merge_arcs(state, branch_by_name, commit_layouts),
        *_lane_change_arcs(branches),
    ]

    # --- Build pull-request list ----------------
    pull_requests = _build_pull_requests(state, branch_by_name, branch_ends)

    # --- Compute grid extent --------------------
    grid = _compute_grid(state, branches, commit_layouts, pull_requests)

    return Layout(
        grid=grid,
        branches=branches,
        commits=commit_layouts,
        arcs=arcs,
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
def _assign_lane_segments(
    state: State,
    branch_starts: dict[str, int],
    line_ends: dict[str, int],
    occ_ends: dict[str, int],
) -> dict[str, list[LaneSegment]]:
    """Assign each branch a sequence of lane segments under `auto_lane_change`.

    Event-sweep packing. A branch *occupies* a lane over `[start, occ_end]`
    and migrates toward lane 0 as lower lanes free, in a fixed priority
    order `(start_row, declaration_index)`. It is a migrating line over
    `[start, line_end]`, then holds that lane for the `(line_end, occ_end]`
    tail — the rows its merge / PR connector reserves (climbing the source
    lane through the merge row, so a sibling may only reclaim the lane
    after it). The occupying set changes only at *boundaries* — a branch's
    `start`, its `line_end + 1` (stops migrating), or its `occ_end + 1`
    (frees its lane). Coalescing equal-lane runs over `[start, line_end]`
    yields the drawn segments; the tail is not drawn (the connector covers
    it).

    Because the order is fixed and lanes only free, a branch's lane is
    non-increasing (downward migration only), and the live branches fill a
    dense block of the lowest lanes. The freeze tail spans
    `theme.merge_lane_clearance` rows (`occ_end - line_end`; default one):
    the line carries all the long travel up to the merge, so the held tail
    stays short regardless of clearance. The forward sweep handles a tail
    of any length by construction — a higher clearance just widens it.

    Args:
        state: The validated state to lay out.
        branch_starts: Commit-axis branch starts from Phase 1.
        line_ends: Row each branch's line is drawn to (from `_branch_extents`).
        occ_ends: Row each branch reserves its lane through (`>= line_end`,
            one further when it feeds a merge / PR).

    Returns:
        Contiguous, ordered `LaneSegment`s per branch name, jointly
        covering each branch's `[start, line_end]` span.
    """
    declaration_index = {name: i for i, name in enumerate(state.branch_order)}

    def priority(name: str) -> tuple[int, int]:
        """Stack key — earlier-born sits lower; declaration order breaks ties."""
        return (branch_starts[name], declaration_index[name])

    boundaries = sorted(
        {branch_starts[name] for name in state.branch_order}
        | {line_ends[name] + 1 for name in state.branch_order}  # migrating → frozen tail
        | {occ_ends[name] + 1 for name in state.branch_order}  # frees its lane
    )

    # Forward sweep low→high so a branch's frozen lane is known before its
    # (single-row) tail is reached.
    frozen_lane: dict[str, int] = {}
    lane_at_boundary: dict[int, dict[str, int]] = {}
    for row in boundaries:
        occupants = sorted(
            (name for name in state.branch_order if branch_starts[name] <= row <= occ_ends[name]),
            key=priority,
        )
        assigned: dict[str, int] = {}
        next_lane = 0
        for name in occupants:
            if row > line_ends[name]:  # connector-reserved tail → hold the line-end lane
                assigned[name] = frozen_lane[name]
                next_lane = max(next_lane, frozen_lane[name] + 1)
            else:  # migrating along its own line → take the next free lane
                assigned[name] = next_lane
                next_lane += 1
        lane_at_boundary[row] = assigned
        for name, lane in assigned.items():
            if row <= line_ends[name]:
                frozen_lane[name] = lane  # remember the lane to hold across the tail

    segments_by_name: dict[str, list[LaneSegment]] = {}
    for name in state.branch_order:
        start, end = branch_starts[name], line_ends[name]
        in_interval = [row for row in boundaries if start <= row <= end]
        segments: list[LaneSegment] = []
        for index, row in enumerate(in_interval):
            seg_end = in_interval[index + 1] - 1 if index + 1 < len(in_interval) else end
            lane = lane_at_boundary[row][name]
            if segments and segments[-1].lane == lane:
                segments[-1].end = seg_end  # coalesce a same-lane run across a boundary
            else:
                segments.append(LaneSegment(lane=lane, start=row, end=seg_end))
        segments_by_name[name] = segments
    return segments_by_name


def _branch_extents(
    state: State,
    commit_pos_by_id: dict[str, int],
    branch_ends: dict[str, int],
    clearance: int,
) -> tuple[dict[str, int], dict[str, int]]:
    """Per-branch line-draw extent and lane-occupancy extent.

    Both start at the branch's last commit and are pushed out by the
    merge / PR connectors it touches (see `_outgoing_connectors`):

    - **`line_end`** — how far the *line* is drawn. The connector's
      **source** reaches `landing_row - 1` (then hops across); its
      **target** reaches `landing_row` (where the connector arrives — a
      no-op for a real merge, whose commit is already there; for an open
      PR it extends the target line to the projected merge point).
    - **`occ_end`** — how far the *lane* is reserved. The **source**
      reserves `clearance` rows past its line (`landing_row - 1 +
      clearance`), because the connector climbs the source lane through
      the merge row; a sibling may reclaim the lane only afterwards. With
      the default `clearance = 1` that is `landing_row` itself. The
      **target** reserves through `landing_row` regardless of clearance (a
      correctness floor for the PR landing, not a spacing knob). So
      `occ_end` is `line_end` for everyone except a connector source.

    Args:
        state: The validated state (commits, parents, open PRs).
        commit_pos_by_id: Commit-axis positions from Phase 1.
        branch_ends: Each branch's last-commit row.
        clearance: Rows a merged / PR'd source holds its lane past its
            drawn line (`theme.merge_lane_clearance`; default `1`).

    Returns:
        `(line_ends, occ_ends)`, each keyed by branch name, with
        `occ_end >= line_end >= branch_ends`.
    """
    line_end = dict(branch_ends)
    occ_end = dict(branch_ends)
    for source, target, landing_row in _outgoing_connectors(state, commit_pos_by_id, branch_ends):
        line_end[source] = max(line_end[source], landing_row - 1)
        line_end[target] = max(line_end[target], landing_row)
        occ_end[source] = max(occ_end[source], landing_row - 1 + clearance)
        occ_end[target] = max(occ_end[target], landing_row)
    return line_end, occ_end


def _outgoing_connectors(
    state: State,
    commit_pos_by_id: dict[str, int],
    branch_ends: dict[str, int],
) -> Iterator[tuple[str, str, int]]:
    """Yield `(source_branch, target_branch, landing_row)` per merge / PR.

    Each is a single-row hop from the source branch's line (one row below
    `landing_row`) onto the target branch at `landing_row`:

    - **Merge** — a merge commit (2+ parents); each merged-in parent's
      branch is a source, the merge commit's branch the target, landing at
      the merge commit's row.
    - **Pull request** — an open PR; `from` is the source, `into` the
      target, landing at the projected merge row (`max(from.end, into.end)
      + 1`, the row a real merge would land at).

    Branch-off connectors are already single-row (parent commit → child
    start one row later) and need no line extension, so they are absent
    here.

    Args:
        state: The validated state (commits, parents, open PRs).
        commit_pos_by_id: Commit-axis positions from Phase 1.
        branch_ends: Each branch's last-commit row (for the PR projection).

    Yields:
        `(source_branch, target_branch, landing_row)` triples.
    """
    for cid, cstate in state.commits.items():
        if len(cstate.parents) < 2:
            continue
        landing_row = commit_pos_by_id.get(cid)
        if landing_row is None:
            continue
        for parent_id in cstate.parents:
            parent = state.commits.get(parent_id)
            if parent is not None and parent.branch != cstate.branch:
                yield parent.branch, cstate.branch, landing_row
    for pr in state.pull_requests.values():
        if pr.from_branch in branch_ends and pr.into_branch in branch_ends:
            yield pr.from_branch, pr.into_branch, max(branch_ends[pr.from_branch], branch_ends[pr.into_branch]) + 1


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
        """Resolve `name`'s lane index, recursing through its ancestor chain first."""
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
                kind=LayoutArcKind.BRANCH_OFF,
                trunk_point=GridSlot(parent_layout.branch_pos, parent_layout.commit_pos),
                branch_point=GridSlot(branch_layout.start_lane, branch_layout.start),
            )
        )
    return arcs


def _merge_arcs(
    state: State,
    branch_by_name: dict[str, LayoutBranch],
    commit_layouts: dict[str, LayoutCommit],
) -> list[LayoutArc]:
    """One merge arc per merged-in parent — a single-row hop into the merge commit.

    The merged-in branch's line has been extended to one row below the
    merge commit (`_line_ends`), so the arc hops from there — on that
    branch's lane at `merge_row - 1` — to the merge commit. The chain
    parent (same branch as the merge commit) is the branch's own
    continuation, not a merge edge, so it is skipped.
    """
    arcs: list[LayoutArc] = []
    for cid, cstate in state.commits.items():
        merge_layout = commit_layouts.get(cid)
        if merge_layout is None or len(cstate.parents) < 2:
            continue
        landing_row = merge_layout.commit_pos
        for parent_id in cstate.parents:
            parent = state.commits.get(parent_id)
            if parent is None or parent.branch == cstate.branch:
                continue
            source = branch_by_name.get(parent.branch)
            if source is None:
                continue
            arcs.append(
                LayoutArc(
                    kind=LayoutArcKind.MERGE,
                    trunk_point=GridSlot(merge_layout.branch_pos, landing_row),
                    branch_point=GridSlot(source.lane_at(landing_row - 1), landing_row - 1),
                )
            )
    return arcs


def _lane_change_arcs(branches: list[LayoutBranch]) -> list[LayoutArc]:
    """One lane-change arc per adjacent segment pair on a migrating branch.

    A branch that occupies more than one lane has a connector bridging
    each pair of consecutive segments. Both endpoints lie on the branch's
    own line: the `trunk_point` is the old-lane tail (`prev.lane,
    prev.end`) and the `branch_point` is the new-lane head (`next.lane,
    next.start`, one row later). The renderer attributes the connector's
    colour from its `branch_point`, so using the new-lane end keeps the
    arc on the migrating branch.
    """
    arcs: list[LayoutArc] = []
    for branch in branches:
        for prev, nxt in zip(branch.segments, branch.segments[1:]):
            arcs.append(
                LayoutArc(
                    kind=LayoutArcKind.LANE_CHANGE,
                    trunk_point=GridSlot(prev.lane, prev.end),
                    branch_point=GridSlot(nxt.lane, nxt.start),
                )
            )
    return arcs


# ==================================================================================================
#  Helpers — pull requests
# ==================================================================================================
def _build_pull_requests(
    state: State,
    branch_by_name: dict[str, LayoutBranch],
    branch_ends: dict[str, int],
) -> list[LayoutPullRequest]:
    """Build one `LayoutPullRequest` per open PR — a single-row hop to the projected merge.

    The projected merge row is `max(from.end, into.end) + 1` (the row a
    real `merge` would land at), using the branches' last-commit rows
    (`branch_ends`) — not the extended line ends, which already fold the
    projection in, so the formula doesn't feed back on itself. The source
    branch's line is extended to one row below the projection, and the PR
    connector hops from there (on the source lane) to the projected merge
    point on the target lane.

    Branches that no longer exist (a clean state should never produce
    this; defensive against partial-validation calls) cause the PR to be
    skipped silently.
    """
    pull_requests: list[LayoutPullRequest] = []
    for pr_id, pr_state in state.pull_requests.items():
        from_branch = branch_by_name.get(pr_state.from_branch)
        into_branch = branch_by_name.get(pr_state.into_branch)
        if from_branch is None or into_branch is None:
            continue
        projected = max(branch_ends[pr_state.from_branch], branch_ends[pr_state.into_branch]) + 1
        pull_requests.append(
            LayoutPullRequest(
                id=pr_id,
                trunk_point=GridSlot(into_branch.lane_at(projected), projected),
                branch_point=GridSlot(from_branch.lane_at(projected - 1), projected - 1),
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

    max_branch_pos = max((seg.lane for b in branches for seg in b.segments), default=0)
    max_commit_pos_from_commits = max((c.commit_pos for c in commit_layouts.values()), default=-1)
    max_commit_pos_from_branches = max((b.end for b in branches), default=-1)
    max_commit_pos_from_prs = max((pr.trunk_point.commit_pos for pr in pull_requests), default=-1)
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
