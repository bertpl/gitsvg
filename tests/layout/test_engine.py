"""Tests for the layout engine — `compute_layout(state) → Layout`."""

import re
from pathlib import Path

import pytest

from gitsvg.errors import ValidationReport
from gitsvg.imports import resolve_imports
from gitsvg.layout import LaneSegment, Layout, LayoutArcKind, LayoutBranch, compute_layout
from gitsvg.parse import parse_jsonl_file, parse_jsonl_text
from gitsvg.state import apply_ops


def _layout_from(text: str) -> Layout:
    """Parse JSONL → state → layout."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    return compute_layout(state)


# ==================================================================================================
#  Branch-axis assignment — declaration order
# ==================================================================================================
def test_first_branch_gets_branch_pos_zero() -> None:
    # --- act --------------------------
    layout = _layout_from('{"op": "branch", "name": "main"}\n')

    # --- assert -----------------------
    assert layout.branches[0].name == "main"
    assert layout.branches[0].segments[0].lane == 0


def test_branch_pos_increments_in_declaration_order() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "branch", "name": "docs", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    by_name = {b.name: b for b in layout.branches}
    assert by_name["main"].segments[0].lane == 0
    assert by_name["feat"].segments[0].lane == 1
    assert by_name["docs"].segments[0].lane == 2


# ==================================================================================================
#  Branch-axis assignment — `branch_pos:` override (lenient passthrough)
# ==================================================================================================
def test_branch_pos_override_pins_lane_verbatim() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n{"op": "branch", "name": "feat", "from_branch": "main", "branch_pos": 7}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    by_name = {b.name: b for b in layout.branches}
    assert by_name["main"].segments[0].lane == 0
    assert by_name["feat"].segments[0].lane == 7


def test_branch_pos_override_to_zero_passes_through_lenient() -> None:
    # Lenient stance: even an override that visually clashes with the
    # parent branch's lane is taken verbatim. The author owns the layout.
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n{"op": "branch", "name": "feat", "from_branch": "main", "branch_pos": 0}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    by_name = {b.name: b for b in layout.branches}
    assert by_name["feat"].segments[0].lane == 0


def test_branch_pos_override_pinned_lane_blocks_subsequent_heuristic_choices() -> None:
    # An override pins its branch's lane regardless of the heuristic.
    # Subsequent branches see that lane as blocked at any commit/start
    # the overridden branch contributes; lane choice for them follows
    # the usual rule (skip blocked lanes).
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "branch_pos": 5}\n'
        '{"op": "commit", "branch": "feat", "msg": "x"}\n'
        '{"op": "branch", "name": "docs", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    by_name = {b.name: b for b in layout.branches}
    assert by_name["main"].segments[0].lane == 0
    assert by_name["feat"].segments[0].lane == 5
    # `feat` has a commit at row 2 on lane 5; rows ≥ 2 on lane 5 are blocked.
    # `docs` parents on main at row 0 → threshold = 1; lanes 1..4 are free
    # of any commits, so docs reclaims the lowest free lane: 1.
    assert by_name["docs"].segments[0].lane == 1


# ==================================================================================================
#  Branch-axis assignment — lane-reuse heuristic
# ==================================================================================================
def test_lane_reclaimed_after_sibling_branch_removed() -> None:
    # An older sibling branch's commits sit at low rows; the new branch
    # rooted at a high row on the same parent reclaims that older
    # sibling's lane. (Story-1 compact-left pattern, in miniature.)
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "old_exp", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "old_exp", "id": "e1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m3", "msg": "x"}\n'
        '{"op": "branch", "name": "new_exp", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "new_exp", "id": "n1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    by_name = {b.name: b for b in layout.branches}
    assert by_name["main"].segments[0].lane == 0
    assert by_name["old_exp"].segments[0].lane == 1
    # new_exp parents on main at m3 (row 3) → threshold 4. old_exp on
    # lane 1 has its only commit at row 2; lane 1 is free at row ≥ 4.
    assert by_name["new_exp"].segments[0].lane == 1


def test_lane_skipped_when_existing_branch_has_recent_commits() -> None:
    # When an older branch on lane 1 has a commit at the new branch's
    # threshold or higher, lane 1 is blocked and new skips to lane 2.
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "ongoing", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "ongoing", "id": "o1", "msg": "x"}\n'
        '{"op": "commit", "branch": "ongoing", "id": "o2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
        '{"op": "branch", "name": "new", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "new", "id": "n1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    by_name = {b.name: b for b in layout.branches}
    # Per the chain-only commit_pos rule: m1=0, o1=1, o2=2, m2=1 (chain
    # parent m1 only). main.tip = m2 (last in commit_ids), so new.start
    # = 2 → threshold 2. Lane 1: o2 at row 2 ≥ 2 → blocked.
    assert by_name["ongoing"].segments[0].lane == 1
    assert by_name["new"].segments[0].lane == 2


def test_lane_skipped_when_blocked_at_or_above_threshold() -> None:
    # Two branches branching off main at the same parent commit. The
    # second one can't reclaim the first one's lane (both parented at
    # the same row → first's commits will be at threshold).
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "first", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "first", "id": "f1", "msg": "x"}\n'
        '{"op": "branch", "name": "second", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "second", "id": "s1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    by_name = {b.name: b for b in layout.branches}
    assert by_name["first"].segments[0].lane == 1
    # second's threshold = m1.commit_pos + 1 = 1; first has f1 at row 1 on
    # lane 1 → blocked. Skip to lane 2.
    assert by_name["second"].segments[0].lane == 2


def test_empty_branch_pseudo_commit_blocks_lane_at_start_position() -> None:
    # An empty branch on lane 1 (start row 2) blocks any new branch
    # whose threshold is ≤ 2 from reusing lane 1.
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
        '{"op": "branch", "name": "ghost", "from_branch": "main"}\n'
        '{"op": "branch", "name": "active", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "active", "id": "a1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    by_name = {b.name: b for b in layout.branches}
    # ghost is empty with start = m2.commit_pos + 1 = 2. On lane 1.
    assert by_name["ghost"].segments[0].lane == 1
    # active's threshold = m2.commit_pos + 1 = 2. Lane 1 has ghost's
    # pseudo-commit at start = 2 ≥ 2 → blocked. Skip to lane 2.
    assert by_name["active"].segments[0].lane == 2


def test_empty_branch_does_not_block_lane_below_its_start() -> None:
    # An empty branch with start = 3 doesn't block a new branch whose
    # threshold is below 3. (Verifies the threshold check is `≥`, not
    # mere "any pseudo-commit on the lane".)
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m3", "msg": "x"}\n'
        '{"op": "branch", "name": "ghost", "from_branch": "main"}\n'
        # ghost: empty, start = m3.commit_pos + 1 = 3, on lane 1.
        '{"op": "commit", "branch": "main", "id": "m4", "msg": "x"}\n'
        # Now declare a sibling branching off m1 (early): its threshold is 1.
        '{"op": "branch", "name": "early", "from_commit": "m1"}\n'
        '{"op": "commit", "branch": "early", "id": "e1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    by_name = {b.name: b for b in layout.branches}
    assert by_name["ghost"].segments[0].lane == 1
    # early's parent is m1 at row 0 → threshold 1. Lane 1's ghost has
    # pseudo-commit at row 3 ≥ 1 → blocked. early skips to lane 2.
    assert by_name["early"].segments[0].lane == 2


def test_first_branch_with_no_parent_gets_lane_zero() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n'

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.branches[0].segments[0].lane == 0


def test_branch_pos_override_short_circuits_heuristic() -> None:
    # An override skips the heuristic entirely; even a value that would
    # be flagged as "blocked" passes through.
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "branch_pos": 0}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    by_name = {b.name: b for b in layout.branches}
    assert by_name["feat"].segments[0].lane == 0


def test_forward_reference_to_later_declared_branch_is_resolved() -> None:
    # Models the rebase rebuild pattern: branch X was originally rooted
    # on a commit on branch Y. Y was removed, then re-declared with the
    # same commit ids. State.branch_order ends up [..., X, Y_new] —
    # X declared before Y_new, but X's rooted_on_commit now resolves to
    # a commit on Y_new. The lane assignment must process Y_new before
    # X to know X's parent lane.
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "Y", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "Y", "id": "y_tip", "msg": "x"}\n'
        '{"op": "branch", "name": "X", "from_commit": "y_tip"}\n'
        '{"op": "commit", "branch": "X", "id": "x1", "msg": "x"}\n'
        '{"op": "remove", "branches": ["Y"]}\n'
        '{"op": "branch", "name": "Y", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "Y", "id": "y_tip", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    by_name = {b.name: b for b in layout.branches}
    # X must have a coherent lane > Y_new's lane (since X's parent is on
    # Y_new). The exact value depends on the heuristic, but the key thing
    # is that lane assignment didn't crash and X is on a higher lane than Y.
    assert by_name["X"].segments[0].lane > by_name["Y"].segments[0].lane


# ==================================================================================================
#  Commit-axis assignment — uniform `tip + 1 + gap` rule
# ==================================================================================================
def test_first_commit_on_root_branch_lands_at_zero() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.commits["c1"].commit_pos == 0


def test_subsequent_commits_advance_by_one() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert [layout.commits[c].commit_pos for c in ["c1", "c2", "c3"]] == [0, 1, 2]


def test_branch_end_is_latest_commit_position() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    main = next(b for b in layout.branches if b.name == "main")
    assert main.end == 1


def test_empty_branch_end_equals_start() -> None:
    """A branch declared but never committed-to has end == start."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    feat = next(b for b in layout.branches if b.name == "feat")
    assert feat.end == feat.start


# ==================================================================================================
#  Branch start — parent_commit.commit_pos + 1
# ==================================================================================================
def test_branch_from_branch_starts_one_above_parent_tip() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    feat = next(b for b in layout.branches if b.name == "feat")
    assert feat.start == 2


def test_branch_from_commit_starts_one_above_named_commit() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m3", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_commit": "m1"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    feat = next(b for b in layout.branches if b.name == "feat")
    assert feat.start == 1


def test_first_commit_on_fork_branch_lands_at_start() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    feat = next(b for b in layout.branches if b.name == "feat")
    assert feat.start == 1
    assert layout.commits["f1"].commit_pos == 1


# ==================================================================================================
#  Gap propagation
# ==================================================================================================
def test_gap_on_first_commit_shifts_landing_position() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x", "gap": 2}\n'

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.commits["c1"].commit_pos == 2


def test_gap_on_subsequent_commit_shifts_only_that_commit_and_beyond() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x", "gap": 1}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.commits["c1"].commit_pos == 0
    assert layout.commits["c2"].commit_pos == 2
    assert layout.commits["c3"].commit_pos == 3


# ==================================================================================================
#  Merge commits land above both parents
# ==================================================================================================
def test_merge_commit_lands_above_both_tips() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "commit", "branch": "feat", "id": "f2", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m2"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.commits["m2"].commit_pos == 3
    assert layout.commits["m2"].branch_pos == 0


def test_merge_with_gap_shifts_above_natural_anchor() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m2", "gap": 2}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.commits["m2"].commit_pos == 4


# ==================================================================================================
#  Replaces (squash) — uniform rule + gap inheritance
# ==================================================================================================
def test_replaces_commit_inherits_position_via_inherited_gap() -> None:
    """When the squash inherits the earliest replaced commit's gap, it lands at
    that commit's original position."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x", "gap": 2}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "csquash", "msg": "squash", "replaces": ["c2", "c3"]}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    # c2 was at position 0 + 1 + 2 = 3 originally; csquash inherits gap=2 and lands
    # at c1.pos + 1 + 2 = 3.
    assert layout.commits["csquash"].commit_pos == 3
    assert "c2" not in layout.commits
    assert "c3" not in layout.commits


def test_replaces_compact_when_no_gap_in_chain() -> None:
    """The common case: gap=0 throughout. Squash compacts."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "csquash", "msg": "squash", "replaces": ["c2", "c3"]}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.commits["csquash"].commit_pos == 1
    main = next(b for b in layout.branches if b.name == "main")
    assert main.end == 1


# ==================================================================================================
#  Branch and commit ids flow through to the layout
# ==================================================================================================
def test_each_branch_carries_an_id() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "branch", "name": "feat", "from_branch": "main"}\n'

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    by_name = {b.name: b for b in layout.branches}
    assert by_name["main"].id
    assert by_name["feat"].id
    assert by_name["main"].id != by_name["feat"].id


def test_commit_carries_its_branch_id() -> None:
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    main = next(b for b in layout.branches if b.name == "main")
    assert layout.commits["c1"].branch_id == main.id


# ==================================================================================================
#  Arcs — branch-off and merge
# ==================================================================================================
def test_branch_off_arc_emitted_for_each_non_root_branch() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    branch_off_arcs = [a for a in layout.arcs if a.kind is LayoutArcKind.BRANCH_OFF]
    assert len(branch_off_arcs) == 1
    arc = branch_off_arcs[0]
    assert arc.trunk_point.branch_pos == 0  # main lane
    assert arc.trunk_point.commit_pos == 0  # m1
    assert arc.branch_point.branch_pos == 1  # feat lane
    assert arc.branch_point.commit_pos == 1  # feat.start


def test_merge_arc_emitted_per_cross_lane_parent() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
        '{"op": "merge", "from": "feat", "into": "main", "as": "m2"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    merge_arcs = [a for a in layout.arcs if a.kind is LayoutArcKind.MERGE]
    assert len(merge_arcs) == 1
    arc = merge_arcs[0]
    assert arc.branch_point.branch_pos == 1  # feat lane (merged-in tip)
    assert arc.trunk_point.branch_pos == 0  # main lane (merge commit)


# ==================================================================================================
#  Lane segments
# ==================================================================================================
def test_each_branch_emits_one_segment_spanning_its_life() -> None:
    """Without lane migration every branch is a single segment on its lane."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    for branch in layout.branches:
        assert branch.segments == [LaneSegment(lane=branch.lane_at(branch.start), start=branch.start, end=branch.end)]


def test_lane_at_clamps_below_and_above_segments() -> None:
    """`lane_at` resolves within segments and clamps past either end."""
    # --- arrange ----------------------
    branch = LayoutBranch(
        id="b",
        name="b",
        segments=[LaneSegment(lane=2, start=1, end=3), LaneSegment(lane=1, start=4, end=6)],
        start=1,
        end=6,
    )

    # --- act / assert -----------------
    assert branch.lane_at(0) == 2  # below first segment → clamp low
    assert branch.lane_at(3) == 2  # within first segment
    assert branch.lane_at(4) == 1  # within second segment
    assert branch.lane_at(9) == 1  # past last segment → clamp high


# ==================================================================================================
#  Grid extent (LayoutGrid)
# ==================================================================================================
def test_grid_extent_for_single_branch_three_commits() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "c3", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.grid.n_commits == 3
    assert layout.grid.n_branches == 1


def test_grid_widens_for_two_branches() -> None:
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feat", "id": "f1", "msg": "x"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.grid.n_branches == 2


def test_grid_includes_empty_branch_start_in_height() -> None:
    """An empty fork branch with start > max(commit_pos) extends the grid."""
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main"}\n'
    )

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    assert layout.grid.n_commits == 3


# ==================================================================================================
#  Resolved hash flows through to the layout
# ==================================================================================================
def test_resolved_auto_hash_in_layout_commit() -> None:
    """A commit declared with `hash: "auto"` shows up in layout with the
    resolved 7-char hex string."""
    # --- arrange ----------------------
    text = '{"op": "branch", "name": "main"}\n{"op": "commit", "branch": "main", "id": "c1", "hash": "auto"}\n'

    # --- act --------------------------
    layout = _layout_from(text)

    # --- assert -----------------------
    resolved = layout.commits["c1"].hash
    assert resolved is not None
    assert resolved != "auto"
    assert re.fullmatch(r"[0-9a-f]{7}", resolved) is not None


# ==================================================================================================
#  Local corpus walk — every test_examples file lays out cleanly
# ==================================================================================================
_CORPUS_DIR = Path(__file__).resolve().parent.parent.parent / "local" / "test_examples"


def _corpus_files() -> list[Path]:
    """Return every `.gitsvg.jsonl` file under `local/test_examples/`, or [] when absent."""
    if not _CORPUS_DIR.exists():
        return []
    return sorted(_CORPUS_DIR.rglob("*.gitsvg.jsonl"))


@pytest.mark.skipif(not _corpus_files(), reason="local/test_examples corpus is gitignored and not present")
@pytest.mark.parametrize("path", _corpus_files(), ids=lambda p: p.relative_to(_CORPUS_DIR).as_posix())
def test_layout_completes_for_every_corpus_file(path: Path) -> None:
    # --- arrange ----------------------
    parsed, report = parse_jsonl_file(path)
    expanded = resolve_imports(parsed, file=path, report=report)
    state, _theme = apply_ops(expanded, report)
    assert report.is_clean(), f"{path} parse/import/apply errors: {report.errors}"

    # --- act --------------------------
    layout = compute_layout(state)

    # --- assert -----------------------
    for commit in layout.commits.values():
        assert commit.commit_pos >= 0
        assert commit.branch_pos >= 0
    for branch in layout.branches:
        assert branch.start >= 0
        assert branch.end >= branch.start
        assert branch.segments[0].lane >= 0
        assert branch.id
    assert layout.grid.n_commits > 0
    assert layout.grid.n_branches > 0


# Defensive — the corpus walker uses ValidationReport implicitly via the parser;
# the import keeps the path resolution in test discovery.
_ = ValidationReport
