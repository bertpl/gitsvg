"""Engine tests for `auto_lane_change` — the event-sweep lane migration.

The flag is exercised through `LayoutSettings(auto_lane_change=True)`;
the off path is the byte-identical single-segment behavior covered by
`test_engine.py` and the example snapshots.
"""

import pytest

from gitsvg.layout import LayoutArcKind, compute_layout
from gitsvg.layout._layout_settings import LayoutSettings
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops

# A scenario that migrates under the flag: `A` branches off `main` and is
# merged back; `C` branches off later and outlives `A`, so it slides down
# into the lane `A` vacates once `A`'s merge connector lands. `main` keeps
# a trailing commit so it stays on lane 0 throughout.
_MIGRATION_TEXT = (
    '{"op": "branch", "name": "main"}\n'
    '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
    '{"op": "branch", "name": "A", "from_branch": "main"}\n'
    '{"op": "commit", "branch": "A", "id": "a1", "msg": "x"}\n'
    '{"op": "branch", "name": "C", "from_branch": "main"}\n'
    '{"op": "commit", "branch": "C", "id": "c1", "msg": "x"}\n'
    '{"op": "merge", "from": "A", "into": "main", "as": "mA", "msg": "x"}\n'
    '{"op": "commit", "branch": "C", "id": "c2", "msg": "x"}\n'
    '{"op": "commit", "branch": "C", "id": "c3", "msg": "x"}\n'
    '{"op": "commit", "branch": "main", "id": "m2", "msg": "x"}\n'
)


def _state(text: str):
    """Parse → apply into a clean `State` (for tests passing custom `LayoutSettings`)."""
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    assert report.is_clean()
    return state


def _layout(text: str, *, auto_lane_change: bool):
    """Parse → state → layout with the given `auto_lane_change` setting."""
    return compute_layout(_state(text), LayoutSettings(auto_lane_change=auto_lane_change))


def _segments(layout, name: str) -> list[tuple[int, int, int]]:
    """Return `(lane, start, end)` tuples for branch `name`."""
    branch = next(b for b in layout.branches if b.name == name)
    return [(s.lane, s.start, s.end) for s in branch.segments]


def _lane_change_arcs(layout) -> list:
    """Return only the lane-change arcs."""
    return [a for a in layout.arcs if a.kind is LayoutArcKind.LANE_CHANGE]


def _assert_no_two_lines_share_a_cell(layout) -> None:
    """Assert no two branch-line segments occupy the same `(lane, row)` cell."""
    seen: dict[tuple[int, int], str] = {}
    for branch in layout.branches:
        for segment in branch.segments:
            for row in range(segment.start, segment.end + 1):
                cell = (segment.lane, row)
                assert cell not in seen, f"{branch.name} overlaps {seen.get(cell)} at {cell}"
                seen[cell] = branch.name


# ==================================================================================================
#  Flag off — unchanged behavior
# ==================================================================================================
def test_flag_off_keeps_single_segment_and_no_lane_change_arcs() -> None:
    """With the flag off a migrating scenario still gives one segment per branch."""
    # --- act --------------------------
    layout = _layout(_MIGRATION_TEXT, auto_lane_change=False)

    # --- assert -----------------------
    for branch in layout.branches:
        assert len(branch.segments) == 1
    assert _lane_change_arcs(layout) == []


# ==================================================================================================
#  Flag on — migration
# ==================================================================================================
def test_branch_migrates_into_freed_lane() -> None:
    """`C` slides 2 → 1 into the lane `A` vacates, one row after `A`'s merge."""
    # --- act --------------------------
    layout = _layout(_MIGRATION_TEXT, auto_lane_change=True)

    # --- assert -----------------------
    assert _segments(layout, "main") == [(0, 0, 3)]
    # A's line runs to row 1 (one below its merge at row 2); its lane stays
    # reserved through the merge row, so C holds lane 2 over rows 1-2 and
    # drops to lane 1 at row 3 — one row of clearance past the merge.
    assert _segments(layout, "A") == [(1, 1, 1)]
    assert _segments(layout, "C") == [(2, 1, 2), (1, 3, 3)]
    assert len(_lane_change_arcs(layout)) == 1


def test_sibling_reclaims_merged_lane_one_row_after_the_merge() -> None:
    """A sibling reclaims a merged branch's lane only one row past the merge — no crowding.

    The merge connector climbs the source lane through the merge row, so
    the lane stays reserved through it; a migrating sibling drops in at
    `merge_row + 1`, never on the merge commit's own row.
    """
    # --- act --------------------------
    layout = _layout(_MIGRATION_TEXT, auto_lane_change=True)

    # --- assert -----------------------
    a = next(b for b in layout.branches if b.name == "A")
    c = next(b for b in layout.branches if b.name == "C")
    merge_row = layout.commits["mA"].commit_pos
    c_on_a_lane = [s for s in c.segments if s.lane == a.start_lane]
    assert len(c_on_a_lane) == 1
    assert c_on_a_lane[0].start == merge_row + 1  # one row of clearance past the merge
    _assert_no_two_lines_share_a_cell(layout)


def test_open_pull_request_extends_source_line_and_holds_its_lane() -> None:
    """An open PR extends the source branch's line to the projected merge row, holding its lane.

    The PR connector is a single-row hop, so the source line itself runs
    up to one row below the projected merge — keeping its lane occupied,
    so a sibling that ends earlier never enters it.
    """
    # --- arrange ----------------------
    # `A` has an open PR into `main`; `C` ends before the projection. `main`
    # is kept far-future via `gap` so it stays on lane 0.
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "A", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "A", "id": "a1", "msg": "x"}\n'
        '{"op": "branch", "name": "C", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "C", "id": "c1", "msg": "x"}\n'
        '{"op": "pull_request", "id": "pr1", "from": "A", "into": "main"}\n'
        '{"op": "commit", "branch": "C", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x", "gap": 3}\n'
    )

    # --- act --------------------------
    layout = _layout(text, auto_lane_change=True)

    # --- assert -----------------------
    pr = layout.pull_requests[0]
    a = next(b for b in layout.branches if b.name == "A")
    c = next(b for b in layout.branches if b.name == "C")
    # A's line is extended to one row below the projected merge point.
    assert a.end == pr.trunk_point.commit_pos - 1
    # C ends before the projection, so it never enters A's lane.
    assert all(s.lane != a.start_lane for s in c.segments)
    _assert_no_two_lines_share_a_cell(layout)


def test_child_branch_sits_above_its_parent_at_birth() -> None:
    """`A` (born off `main`) lands on a higher lane than `main` at its start row."""
    # --- act --------------------------
    layout = _layout(_MIGRATION_TEXT, auto_lane_change=True)

    # --- assert -----------------------
    main = next(b for b in layout.branches if b.name == "main")
    a = next(b for b in layout.branches if b.name == "A")
    assert a.start_lane > main.lane_at(a.start)


def test_commit_lane_follows_its_segment() -> None:
    """A commit on a migrated stretch carries the migrated lane, not the birth lane."""
    # --- act --------------------------
    layout = _layout(_MIGRATION_TEXT, auto_lane_change=True)

    # --- assert -----------------------
    # c1 is on C's first segment (lane 2); c3 is on the migrated segment (lane 1).
    assert layout.commits["c1"].branch_pos == 2
    assert layout.commits["c3"].branch_pos == 1


def test_lane_change_arc_endpoints_step_downward_by_one_row() -> None:
    """Each lane-change arc bridges `(old_lane, r-1) → (new_lane, r)`, new lane lower."""
    # --- act --------------------------
    layout = _layout(_MIGRATION_TEXT, auto_lane_change=True)

    # --- assert -----------------------
    for arc in _lane_change_arcs(layout):
        assert arc.branch_point.commit_pos == arc.trunk_point.commit_pos + 1
        assert arc.branch_point.branch_pos < arc.trunk_point.branch_pos


def test_older_branch_merging_mid_life_keeps_lines_disjoint() -> None:
    """An older branch merging while a younger one is still migrating must not overlap it.

    `Z` (older) merges after `X`'s (younger) last commit; `W` sits
    outermost and migrates inward as lanes free. Single-row connectors
    mean every branch is just a line, so the sweep keeps all lines on
    distinct cells.
    """
    # --- arrange ----------------------
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "Z", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "Z", "id": "z1", "msg": "x"}\n'
        '{"op": "branch", "name": "X", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "X", "id": "x1", "msg": "x"}\n'
        '{"op": "branch", "name": "W", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "W", "id": "w1", "msg": "x"}\n'
        '{"op": "commit", "branch": "Z", "id": "z2", "msg": "x"}\n'
        '{"op": "merge", "from": "Z", "into": "main", "as": "mZ", "msg": "x"}\n'
        '{"op": "commit", "branch": "W", "id": "w2", "msg": "x"}\n'
        '{"op": "merge", "from": "X", "into": "main", "as": "mX", "msg": "x"}\n'
        '{"op": "commit", "branch": "W", "id": "w3", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x", "gap": 2}\n'
    )

    # --- act --------------------------
    layout = _layout(text, auto_lane_change=True)

    # --- assert -----------------------
    _assert_no_two_lines_share_a_cell(layout)


def test_multi_lane_drop_in_a_single_step() -> None:
    """When two lower lanes free at one boundary, the survivor drops two lanes at once."""
    # --- arrange ----------------------
    # `A` and `B` dangle (last commit, never merged) on the same row, so both
    # free at the same boundary. `main` keeps a far-future commit (via `gap`)
    # so it stays on lane 0 while `C` collapses from lane 3 straight to lane 1.
    text = (
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "A", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "A", "id": "a1", "msg": "x"}\n'
        '{"op": "branch", "name": "B", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "B", "id": "b1", "msg": "x"}\n'
        '{"op": "branch", "name": "C", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "C", "id": "c1", "msg": "x"}\n'
        '{"op": "commit", "branch": "C", "id": "c2", "msg": "x"}\n'
        '{"op": "commit", "branch": "main", "id": "m2", "msg": "x", "gap": 3}\n'
    )

    # --- act --------------------------
    layout = _layout(text, auto_lane_change=True)

    # --- assert -----------------------
    assert _segments(layout, "C") == [(3, 1, 1), (1, 2, 2)]
    arcs = _lane_change_arcs(layout)
    assert len(arcs) == 1
    assert arcs[0].trunk_point.branch_pos == 3
    assert arcs[0].branch_point.branch_pos == 1


# ==================================================================================================
#  Sweep regression coverage — cases the static heuristic special-cases
# ==================================================================================================
def test_empty_branch_is_a_single_segment() -> None:
    """An empty branch (no commits) is one zero-length segment and never migrates."""
    # --- act --------------------------
    layout = _layout(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "scratch", "from_branch": "main"}\n',
        auto_lane_change=True,
    )

    # --- assert -----------------------
    scratch = _segments(layout, "scratch")
    assert len(scratch) == 1
    assert scratch[0][1] == scratch[0][2]  # start == end (zero-length)


def test_forward_reference_completes_under_the_sweep() -> None:
    """A child branching off a commit declared on a later-removed-then-rebuilt branch lays out cleanly."""
    # --- act --------------------------
    layout = _layout(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feature", "from_branch": "main"}\n'
        '{"op": "commit", "branch": "feature", "id": "f1", "msg": "x"}\n'
        '{"op": "remove", "branches": ["feature"]}\n'
        '{"op": "branch", "name": "feature", "from_commit": "m1"}\n'
        '{"op": "commit", "branch": "feature", "id": "f2", "msg": "x"}\n',
        auto_lane_change=True,
    )

    # --- assert -----------------------
    # Every branch's segments jointly cover its span with no gaps.
    for branch in layout.branches:
        rows = [r for s in branch.segments for r in range(s.start, s.end + 1)]
        assert rows == list(range(branch.start, branch.end + 1))


def test_composes_with_unique_commit_rows() -> None:
    """`auto_lane_change` and `commit_row_mode = unique` compose without error."""
    # --- arrange ----------------------
    from gitsvg._shared.value_types import CommitRowMode

    parsed, report = parse_jsonl_text(_MIGRATION_TEXT, file="x.jsonl")
    state, _theme = apply_ops(parsed, report)
    settings = LayoutSettings(auto_lane_change=True, commit_row_mode=CommitRowMode.UNIQUE)

    # --- act --------------------------
    layout = compute_layout(state, settings)

    # --- assert -----------------------
    # C still migrates (more than one segment) with unique rows in force.
    assert len(next(b for b in layout.branches if b.name == "C").segments) > 1


# ==================================================================================================
#  merge_lane_clearance — how far a merged source holds its lane
# ==================================================================================================
# `A` merges into `main`; `C` (longer-lived) migrates into the lane `A`
# frees. `C` reclaims that lane at `merge_row + clearance`. Gaps keep `C`
# alive well past the widest clearance under test and keep `main` on lane 0.
_CLEARANCE_TEXT = (
    '{"op": "branch", "name": "main"}\n'
    '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
    '{"op": "branch", "name": "A", "from_branch": "main"}\n'
    '{"op": "commit", "branch": "A", "id": "a1", "msg": "x"}\n'
    '{"op": "branch", "name": "C", "from_branch": "main"}\n'
    '{"op": "commit", "branch": "C", "id": "c1", "msg": "x"}\n'
    '{"op": "merge", "from": "A", "into": "main", "as": "mA", "msg": "x"}\n'
    '{"op": "commit", "branch": "C", "id": "c2", "msg": "x", "gap": 1}\n'
    '{"op": "commit", "branch": "C", "id": "c3", "msg": "x"}\n'
    '{"op": "commit", "branch": "C", "id": "c4", "msg": "x"}\n'
    '{"op": "commit", "branch": "main", "id": "m2", "msg": "x", "gap": 5}\n'
)


@pytest.mark.parametrize("clearance", [0, 1, 2])
def test_sibling_reclaims_freed_lane_at_merge_row_plus_clearance(clearance: int) -> None:
    """`C` reclaims `A`'s lane exactly `clearance` rows past the merge."""
    # --- act --------------------------
    layout = compute_layout(
        _state(_CLEARANCE_TEXT),
        LayoutSettings(auto_lane_change=True, merge_lane_clearance=clearance),
    )

    # --- assert -----------------------
    merge_row = layout.commits["mA"].commit_pos
    a_lane = next(b for b in layout.branches if b.name == "A").start_lane
    c = next(b for b in layout.branches if b.name == "C")
    reclaimed = [s for s in c.segments if s.lane == a_lane]
    assert len(reclaimed) == 1
    assert reclaimed[0].start == merge_row + clearance
    _assert_no_two_lines_share_a_cell(layout)


def test_default_clearance_matches_explicit_one() -> None:
    """Omitting `merge_lane_clearance` is identical to setting it to `1`."""
    # --- arrange ----------------------
    state = _state(_CLEARANCE_TEXT)

    # --- act --------------------------
    default = compute_layout(state, LayoutSettings(auto_lane_change=True))
    explicit_one = compute_layout(state, LayoutSettings(auto_lane_change=True, merge_lane_clearance=1))

    # --- assert -----------------------
    assert _segments(default, "C") == _segments(explicit_one, "C")
