"""JSON serialisation of resolved layout.

`layout_to_json` produces `gitsvg layout`'s **public output schema** — a
deliberate, stable contract for consumers (agents, tooling) debugging a
diagram's placement, kept independent of the internal `Layout`
dataclasses at `gitsvg/layout/_layout.py` so internal refactors don't
churn it:

- `grid` — integer-grid extent: `n_commits`, `n_branches`.
- `branches` — one entry per declared branch, with the opaque internal
  id, the user-facing name, and the lane / start / end slot positions.
- `commits` — one entry per surviving commit, with lane / row positions
  and the branch id the commit lives on.
- `arcs` — pre-computed connectors (branch-off and merge), in z-order.
  Each carries a `kind` (`"branch_off"` / `"merge"`) and `from_*` / `to_*`
  endpoint slots — the orientation a reader debugging a layout reads most
  naturally. Internally a connector is a trunk point and a branch point;
  `_arc_to_json` maps the pair back to the public schema.
- `pull_requests` — geometry for each open pull request: `from_*` (source
  tip) and `to_*` (projected merge point on the target lane).

`grid` / `branches` / `commits` still serialise straight from their
dataclasses via `dataclasses.asdict` (the commits dict flattens to a
list, each entry carrying its own `id`, so all collections share a
uniform shape); `arcs` and `pull_requests` are translated explicitly so
the public field names stay the user-facing `from` / `to` / `kind` ones
rather than the internal trunk / branch terms.
"""

import dataclasses
from typing import Any

from gitsvg.layout._layout import Layout, LayoutArc, LayoutPullRequest


def _arc_to_json(arc: LayoutArc) -> dict[str, Any]:
    """Map a connector's trunk / branch points to the public from/to/kind schema.

    The branch point above the trunk point (higher commit-axis index) is
    a branch-off, at or below is a merge — the same derivation the
    renderer uses. The `from` end is the parent commit for a branch-off
    and the merged-in tip for a merge; the `to` end is the other point.

    Args:
        arc: The connector to serialise.

    Returns:
        A dict with `kind`, `from_branch_pos`, `from_commit_pos`,
        `to_branch_pos`, `to_commit_pos`.
    """
    if arc.branch_point.commit_pos > arc.trunk_point.commit_pos:
        kind, from_point, to_point = "branch_off", arc.trunk_point, arc.branch_point
    else:
        kind, from_point, to_point = "merge", arc.branch_point, arc.trunk_point
    return {
        "kind": kind,
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
        pr: The pull request to serialise.

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
    """Convert a resolved `Layout` to a JSON-serialisable dict.

    Args:
        layout: The layout produced by `compute_layout`.

    Returns:
        A nested dict with `grid`, `branches`, `commits`, `arcs`,
        and `pull_requests` top-level keys. The dict is
        `json.dumps`-able with no custom encoder.
    """
    return {
        "grid": dataclasses.asdict(layout.grid),
        "branches": [dataclasses.asdict(b) for b in layout.branches],
        "commits": [dataclasses.asdict(c) for c in layout.commits.values()],
        "arcs": [_arc_to_json(a) for a in layout.arcs],
        "pull_requests": [_pull_request_to_json(p) for p in layout.pull_requests],
    }
