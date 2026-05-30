"""Tests for the render-side lookups derived from `Layout.branches`.

`_branch_through_point` resolves a connector's branch point back to the
branch whose colour the renderer should use — the colour attribution
that moved render-side when the layout DTOs dropped their
`color_branch_id` fields. A branch-off's branch point is the new
branch's start; a merge's or pull request's branch point is a row within
the merged-in / source branch's life.

`_get_occupied_lanes` enumerates the lanes the renderer draws guides at,
derived from the same branch index.
"""

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render._renderer import _branch_through_point, _get_occupied_lanes
from gitsvg.state import apply_ops


def _layout_from(text: str):
    """Parse JSONL → state → layout, for arrange blocks in this file."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    return compute_layout(state)


# ==================================================================================================
#  _branch_through_point — colour attribution via a connector's branch point
# ==================================================================================================
def test_branch_through_point_resolves_new_branch_for_branch_off() -> None:
    # --- arrange ----------------------
    layout = _layout_from(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )
    # branch-off: branch point above the trunk point.
    arc = next(a for a in layout.arcs if a.branch_point.commit_pos > a.trunk_point.commit_pos)
    feat = next(b for b in layout.branches if b.name == "feat")

    # --- act --------------------------
    resolved = _branch_through_point(layout, arc.branch_point)

    # --- assert -----------------------
    assert resolved.id == feat.id


def test_branch_through_point_resolves_source_branch_for_merge() -> None:
    # --- arrange ----------------------
    layout = _layout_from(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m2"}\n'
    )
    # merge: branch point below the trunk point.
    arc = next(a for a in layout.arcs if a.branch_point.commit_pos < a.trunk_point.commit_pos)
    feat = next(b for b in layout.branches if b.name == "feat")

    # --- act --------------------------
    resolved = _branch_through_point(layout, arc.branch_point)

    # --- assert -----------------------
    assert resolved.id == feat.id


def test_branch_through_point_resolves_source_branch_for_pull_request() -> None:
    # --- arrange ----------------------
    layout = _layout_from(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "pull_request", "from": "feat", "into": "main", "id": "pr1"}\n'
    )
    pr = layout.pull_requests[0]
    feat = next(b for b in layout.branches if b.name == "feat")

    # --- act --------------------------
    resolved = _branch_through_point(layout, pr.branch_point)

    # --- assert -----------------------
    assert resolved.id == feat.id


# ==================================================================================================
#  _get_occupied_lanes — sorted dedup of branch lanes
# ==================================================================================================
def test_get_occupied_lanes_one_per_unique_branch_pos() -> None:
    # --- arrange / act ----------------
    layout = _layout_from(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "branch", "name": "docs", "from_branch": "main"}\n'
    )

    # --- assert -----------------------
    assert _get_occupied_lanes(layout) == [0, 1, 2]
