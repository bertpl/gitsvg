"""Tests for the render-side lookups derived from `Layout.branches`.

`_get_color_branch_of_arc` and `_get_color_branch_of_pull_request`
resolve a connector back to the branch whose colour the renderer
should use — moved here when the layout DTOs dropped their
`color_branch_id` fields. Colour attribution is now a renderer
concern, derived from the arc's `kind` plus the layout's branch
index.

`_get_occupied_lanes` enumerates the lanes the renderer draws guides
at, derived from the same branch index.
"""

from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render._renderer import _get_color_branch_of_arc, _get_color_branch_of_pull_request, _get_occupied_lanes
from gitsvg.state import apply_ops


def _layout_from(text: str):
    """Parse JSONL → state → layout, for arrange blocks in this file."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    return compute_layout(state)


# ==================================================================================================
#  _get_color_branch_of_arc — branch-off vs merge attribution
# ==================================================================================================
def test_get_color_branch_of_arc_returns_target_branch_on_branch_off() -> None:
    # --- arrange ----------------------
    layout = _layout_from(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )
    arc = next(a for a in layout.arcs if a.kind == "branch_off")
    feat = next(b for b in layout.branches if b.name == "feat")

    # --- act --------------------------
    resolved = _get_color_branch_of_arc(layout, arc)

    # --- assert -----------------------
    assert resolved.id == feat.id


def test_get_color_branch_of_arc_returns_source_branch_on_merge() -> None:
    # --- arrange ----------------------
    layout = _layout_from(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m2"}\n'
    )
    arc = next(a for a in layout.arcs if a.kind == "merge")
    feat = next(b for b in layout.branches if b.name == "feat")

    # --- act --------------------------
    resolved = _get_color_branch_of_arc(layout, arc)

    # --- assert -----------------------
    assert resolved.id == feat.id


# ==================================================================================================
#  _get_color_branch_of_pull_request — source branch attribution
# ==================================================================================================
def test_get_color_branch_of_pull_request_returns_source_branch() -> None:
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
    resolved = _get_color_branch_of_pull_request(layout, pr)

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
