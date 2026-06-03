"""JSON serialization of resolved layout.

`layout_to_json` produces `gitsvg layout`'s **public output schema** — a
deliberate, stable contract for consumers (agents, tooling) debugging a
diagram's placement, kept independent of the internal `Layout`
dataclasses at `gitsvg/layout/_layout.py` so internal refactors don't
churn it:

- `grid` — integer-grid extent: `n_commits`, `n_branches`.
- `branches` — one entry per declared branch, with the opaque internal
  id, the user-facing name, and the lane / start / end slot positions.
- `commits` — one entry per surviving commit, with lane / row positions,
  the branch id the commit lives on, and an `is_merge` flag (2+ parents).
- `arcs` — pre-computed connectors (branch-off, merge, and lane-change), in z-order.
  Each carries a `kind` (`"branch_off"` / `"merge"` / `"lane_change"`) and `from_*` / `to_*`
  endpoint slots — the orientation a reader debugging a layout reads most
  naturally. Internally a connector is a trunk point and a branch point;
  `_arc_to_json` maps the pair back to the public schema.
- `pull_requests` — geometry for each open pull request: `from_*` (source
  tip) and `to_*` (projected merge point on the target lane).

`grid` / `commits` serialize straight from their dataclasses via
`dataclasses.asdict` (the commits dict flattens to a list, each entry
carrying its own `id`, so all collections share a uniform schema).
`branches` are translated explicitly (`_branch_to_json`) so the public
schema stays the single lane / start / end view even though the internal
`LayoutBranch` now carries a list of lane segments. `arcs` and
`pull_requests` are translated explicitly too so the public field names
stay the user-facing `from` / `to` / `kind` ones rather than the
internal trunk / branch terms.
"""

import dataclasses
from typing import Any

from ._layout import Layout, LayoutArc, LayoutBranch, LayoutPullRequest
from ._layout_arc_kind import LayoutArcKind


def _branch_to_json(branch: LayoutBranch) -> dict[str, Any]:
    """Map a branch to the public id/name/lane/start/end schema.

    `branch_pos` is the lane the branch occupies at its start row; for a
    static-lane branch it is the single lane. `segments` carries the full
    per-lane breakdown — one entry for a static branch, several when the
    branch migrated lanes under `auto_lane_change`.

    Args:
        branch: The branch to serialize.

    Returns:
        A dict with `id`, `name`, `branch_pos`, `segments`, `start`,
        `end`, `tip_commit_id`.
    """
    return {
        "id": branch.id,
        "name": branch.name,
        "branch_pos": branch.start_lane,
        "segments": [{"lane": s.lane, "start": s.start, "end": s.end} for s in branch.segments],
        "start": branch.start,
        "end": branch.end,
        "tip_commit_id": branch.tip_commit_id,
    }


def _arc_to_json(arc: LayoutArc) -> dict[str, Any]:
    """Map a connector's trunk / branch points to the public from/to/kind schema.

    `kind` comes straight off the connector. For a branch-off the `from`
    end is the parent commit (the trunk) and the `to` end is the new
    branch's start; for a merge the `from` end is the merged-in tip (the
    branch point) and the `to` end is the merge commit; for a lane-change
    the `from` end is the old-lane tail (the trunk) and the `to` end is
    the new-lane head (the branch point).

    Args:
        arc: The connector to serialize.

    Returns:
        A dict with `kind`, `from_branch_pos`, `from_commit_pos`,
        `to_branch_pos`, `to_commit_pos`.

    Raises:
        ValueError: If `arc.kind` is a kind this serializer does not map
            to a `from` / `to` orientation.
    """
    if arc.kind is LayoutArcKind.MERGE:
        from_point, to_point = arc.branch_point, arc.trunk_point
    elif arc.kind in (LayoutArcKind.BRANCH_OFF, LayoutArcKind.LANE_CHANGE):
        from_point, to_point = arc.trunk_point, arc.branch_point
    else:
        raise ValueError(f"_arc_to_json does not handle arc kind {arc.kind!r}")
    return {
        "kind": str(arc.kind),
        "from_branch_pos": from_point.branch_pos,
        "from_commit_pos": from_point.commit_pos,
        "to_branch_pos": to_point.branch_pos,
        "to_commit_pos": to_point.commit_pos,
    }


def _pull_request_to_json(pr: LayoutPullRequest) -> dict[str, Any]:
    """Map a pull request to the public from/to schema.

    The `from` end is the source tip (the layout's branch point); the
    `to` end is the projected merge point on the target lane (the trunk
    point). A pull request is always the merge orientation, so it carries
    no `kind`.

    Args:
        pr: The pull request to serialize.

    Returns:
        A dict with `id`, `from_branch_pos`, `from_commit_pos`,
        `to_branch_pos`, `to_commit_pos`, `title`.
    """
    return {
        "id": pr.id,
        "from_branch_pos": pr.branch_point.branch_pos,
        "from_commit_pos": pr.branch_point.commit_pos,
        "to_branch_pos": pr.trunk_point.branch_pos,
        "to_commit_pos": pr.trunk_point.commit_pos,
        "title": pr.title,
    }


def layout_to_json(layout: Layout) -> dict[str, Any]:
    """Convert a resolved `Layout` to a JSON-serializable dict.

    Args:
        layout: The layout produced by `compute_layout`.

    Returns:
        A nested dict with `grid`, `branches`, `commits`, `arcs`,
        and `pull_requests` top-level keys. The dict is
        `json.dumps`-able with no custom encoder.
    """
    return {
        "grid": dataclasses.asdict(layout.grid),
        "branches": [_branch_to_json(b) for b in layout.branches],
        "commits": [dataclasses.asdict(c) for c in layout.commits.values()],
        "arcs": [_arc_to_json(a) for a in layout.arcs],
        "pull_requests": [_pull_request_to_json(p) for p in layout.pull_requests],
    }
