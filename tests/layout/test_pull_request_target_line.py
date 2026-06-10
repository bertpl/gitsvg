"""Tests for `pull_request_extend_target_line` — the open-PR target-line extent toggle."""

from gitsvg.layout import Layout, compute_layout
from gitsvg.layout._layout_settings import LayoutSettings
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops

PR_TEXT = (
    '{"op": "branch", "name": "main"}\n'
    '{"op": "commit", "branch": "main", "id": "m1", "msg": "first"}\n'
    '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    '{"op": "commit", "branch": "feat", "id": "f1", "msg": "wip"}\n'
    '{"op": "pull_request", "id": "pr1", "from": "feat", "into": "main", "title": "Add the thing"}\n'
)

MERGE_TEXT = (
    '{"op": "branch", "name": "main"}\n'
    '{"op": "commit", "branch": "main", "id": "m1", "msg": "first"}\n'
    '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    '{"op": "commit", "branch": "feat", "id": "f1", "msg": "wip"}\n'
    '{"op": "merge", "from": "feat", "into": "main", "as": "m2"}\n'
)


def _layout_from(text: str, layout_settings: LayoutSettings | None = None) -> Layout:
    """Parse JSONL → state → layout, asserting clean validation."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    assert report.is_clean(), f"unexpected errors: {[e.format() for e in report.errors]}"
    return compute_layout(state, layout_settings)


def _line_end(layout: Layout, name: str) -> int:
    """Return how far `name`'s drawn line reaches (its last segment's end row)."""
    by_name = {b.name: b for b in layout.branches}
    return by_name[name].segments[-1].end


# ==================================================================================================
#  Open PR — the toggle governs the target line's extent
# ==================================================================================================
def test_default_pr_target_line_ends_at_tip_commit() -> None:
    # --- act --------------------------
    layout = _layout_from(PR_TEXT)

    # --- assert -----------------------
    # The connector still lands one row past the latest tip; the target
    # line stops at its own tip commit, so the dash lands in the void.
    projected = layout.pull_requests[0].trunk_point.commit_pos
    assert _line_end(layout, "main") == layout.commits["m1"].commit_pos
    assert _line_end(layout, "main") < projected


def test_extended_pr_target_line_reaches_projected_merge_row() -> None:
    # --- act --------------------------
    layout = _layout_from(PR_TEXT, LayoutSettings(pull_request_extend_target_line=True))

    # --- assert -----------------------
    assert _line_end(layout, "main") == layout.pull_requests[0].trunk_point.commit_pos


def test_pr_source_line_reaches_hop_row_in_both_modes() -> None:
    # --- act --------------------------
    layout_off = _layout_from(PR_TEXT)
    layout_on = _layout_from(PR_TEXT, LayoutSettings(pull_request_extend_target_line=True))

    # --- assert -----------------------
    # The source line carries the vertical travel to one row below the
    # projected merge point regardless of the target-line toggle.
    hop_row = layout_off.pull_requests[0].branch_point.commit_pos
    assert _line_end(layout_off, "feat") == hop_row
    assert _line_end(layout_on, "feat") == hop_row


def test_toggle_changes_only_the_target_line_extent() -> None:
    """Cosmetic toggle — connector geometry, lanes, and grid extent are identical."""
    # --- act --------------------------
    layout_off = _layout_from(PR_TEXT)
    layout_on = _layout_from(PR_TEXT, LayoutSettings(pull_request_extend_target_line=True))

    # --- assert -----------------------
    assert layout_off.pull_requests == layout_on.pull_requests
    assert layout_off.grid == layout_on.grid
    lanes_off = {b.name: [s.lane for s in b.segments] for b in layout_off.branches}
    lanes_on = {b.name: [s.lane for s in b.segments] for b in layout_on.branches}
    assert lanes_off == lanes_on


# ==================================================================================================
#  Real merge — unaffected by construction (the merge commit sits on the target)
# ==================================================================================================
def test_merge_layout_is_identical_in_both_modes() -> None:
    # --- act --------------------------
    layout_off = _layout_from(MERGE_TEXT)
    layout_on = _layout_from(MERGE_TEXT, LayoutSettings(pull_request_extend_target_line=True))

    # --- assert -----------------------
    assert layout_off == layout_on
    assert _line_end(layout_off, "main") == layout_off.commits["m2"].commit_pos
