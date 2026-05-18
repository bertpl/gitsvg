"""JSON serialisation of resolved layout.

`layout_to_json` produces a dict matching `gitsvg layout`'s public
output schema — a direct mirror of the `Layout` dataclass at
`gitsvg/layout/_layout.py`:

- `grid` — integer-grid extent: `n_commits`, `n_branches`.
- `branches` — one entry per declared branch, with the opaque
  internal id, the user-facing name, the lane index, and the
  resolved label side.
- `commits` — one entry per surviving commit, with lane / row
  positions and the branch id the commit lives on.
- `arcs` — pre-computed connectors (branch-off and merge) as slot
  pairs, in z-order.
- `guides` — one entry per occupied lane.
- `pull_requests` — geometry for each open pull request (source tip
  → projected merge point on the target lane).

The dataclass has `commits` as a dict keyed by id for renderer
lookup convenience; the JSON view emits it as a list (each entry
carries its own `id`) so all collections share a uniform shape.
"""

import dataclasses
from typing import Any

from gitsvg.layout._layout import Layout


def layout_to_json(layout: Layout) -> dict[str, Any]:
    """Convert a resolved `Layout` to a JSON-serialisable dict.

    Args:
        layout: The layout produced by `compute_layout`.

    Returns:
        A nested dict with `grid`, `branches`, `commits`, `arcs`,
        `guides`, and `pull_requests` top-level keys. The dict is
        `json.dumps`-able with no custom encoder.
    """
    return {
        "grid": dataclasses.asdict(layout.grid),
        "branches": [dataclasses.asdict(b) for b in layout.branches],
        "commits": [dataclasses.asdict(c) for c in layout.commits.values()],
        "arcs": [dataclasses.asdict(a) for a in layout.arcs],
        "guides": [dataclasses.asdict(g) for g in layout.guides],
        "pull_requests": [dataclasses.asdict(p) for p in layout.pull_requests],
    }
