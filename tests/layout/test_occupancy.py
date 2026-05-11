"""Tests for `gitsvg.layout._occupancy.Occupancy`.

Public API only. Storage shape is private and never asserted on.
"""

import pytest

from gitsvg.layout._occupancy import Occupancy


# ==================================================================================================
#  Construction
# ==================================================================================================
def test_empty_occupancy_has_no_points() -> None:
    # --- arrange / act ----------------
    occ = Occupancy()

    # --- assert -----------------------
    assert occ.occupied_lanes() == []
    assert list(occ) == []
    assert not occ.is_occupied(0, 0)
    assert not occ.is_blocked_at_or_after(0, 0)
    assert occ.occupied_rows_on(0) == frozenset()


# ==================================================================================================
#  add() and is_occupied()
# ==================================================================================================
def test_add_then_is_occupied() -> None:
    # --- arrange ----------------------
    occ = Occupancy()

    # --- act --------------------------
    occ.add(2, 5)

    # --- assert -----------------------
    assert occ.is_occupied(2, 5)
    assert not occ.is_occupied(2, 4)
    assert not occ.is_occupied(2, 6)
    assert not occ.is_occupied(1, 5)
    assert not occ.is_occupied(3, 5)


def test_add_is_idempotent() -> None:
    # --- arrange ----------------------
    occ = Occupancy()

    # --- act --------------------------
    occ.add(1, 3)
    occ.add(1, 3)
    occ.add(1, 3)

    # --- assert -----------------------
    assert occ.is_occupied(1, 3)
    assert occ.occupied_rows_on(1) == frozenset({3})
    assert list(occ) == [(1, 3)]


# ==================================================================================================
#  is_blocked_at_or_after()
# ==================================================================================================
def test_is_blocked_at_or_after_on_empty_lane() -> None:
    # --- arrange / act ----------------
    occ = Occupancy()

    # --- assert -----------------------
    assert not occ.is_blocked_at_or_after(0, 0)
    assert not occ.is_blocked_at_or_after(7, 100)


@pytest.mark.parametrize(
    ("threshold", "expected"),
    [
        (0, True),  # any row at or above 0 — yes
        (3, True),  # row 5 is at or above 3 — yes
        (5, True),  # row 5 is exactly at threshold — yes
        (6, False),  # row 5 is below 6 — no
        (100, False),
    ],
)
def test_is_blocked_at_or_after_thresholds(threshold: int, expected: bool) -> None:
    # --- arrange ----------------------
    occ = Occupancy()
    occ.add(2, 5)

    # --- act / assert -----------------
    assert occ.is_blocked_at_or_after(2, threshold) is expected


def test_is_blocked_at_or_after_only_inspects_named_lane() -> None:
    # --- arrange ----------------------
    occ = Occupancy()
    occ.add(0, 10)
    occ.add(2, 10)

    # --- act / assert -----------------
    assert occ.is_blocked_at_or_after(0, 5)
    assert not occ.is_blocked_at_or_after(1, 5)  # lane 1 is empty
    assert occ.is_blocked_at_or_after(2, 5)
    assert not occ.is_blocked_at_or_after(3, 5)


def test_is_blocked_at_or_after_picks_max_row_on_lane() -> None:
    """A lane with several points is blocked iff the *max* row is ≥ threshold."""
    # --- arrange ----------------------
    occ = Occupancy()
    occ.add(1, 2)
    occ.add(1, 7)
    occ.add(1, 4)

    # --- act / assert -----------------
    assert occ.is_blocked_at_or_after(1, 7)
    assert occ.is_blocked_at_or_after(1, 5)  # row 7 satisfies
    assert not occ.is_blocked_at_or_after(1, 8)


# ==================================================================================================
#  occupied_rows_on() and occupied_lanes()
# ==================================================================================================
def test_occupied_rows_on_returns_frozenset_copy() -> None:
    # --- arrange ----------------------
    occ = Occupancy()
    occ.add(3, 1)
    occ.add(3, 4)
    occ.add(3, 9)

    # --- act --------------------------
    rows = occ.occupied_rows_on(3)

    # --- assert -----------------------
    assert rows == frozenset({1, 4, 9})
    assert isinstance(rows, frozenset)


def test_occupied_rows_on_empty_lane_returns_empty_frozenset() -> None:
    # --- arrange / act ----------------
    occ = Occupancy()
    occ.add(0, 0)

    # --- assert -----------------------
    assert occ.occupied_rows_on(99) == frozenset()


def test_occupied_lanes_returns_sorted_list() -> None:
    # --- arrange ----------------------
    occ = Occupancy()
    occ.add(5, 0)
    occ.add(0, 0)
    occ.add(3, 0)
    occ.add(1, 0)

    # --- act --------------------------
    lanes = occ.occupied_lanes()

    # --- assert -----------------------
    assert lanes == [0, 1, 3, 5]
    assert isinstance(lanes, list)


def test_occupied_lanes_deduplicates() -> None:
    """A lane with multiple rows appears in occupied_lanes() exactly once."""
    # --- arrange ----------------------
    occ = Occupancy()
    occ.add(2, 1)
    occ.add(2, 5)
    occ.add(2, 9)

    # --- act / assert -----------------
    assert occ.occupied_lanes() == [2]


# ==================================================================================================
#  __iter__()
# ==================================================================================================
def test_iter_yields_every_added_point_exactly_once() -> None:
    # --- arrange ----------------------
    occ = Occupancy()
    occ.add(2, 3)
    occ.add(0, 1)
    occ.add(2, 1)
    occ.add(0, 5)

    # --- act --------------------------
    points = list(occ)

    # --- assert -----------------------
    assert set(points) == {(0, 1), (0, 5), (2, 1), (2, 3)}
    assert len(points) == 4


def test_iter_order_is_sorted_lane_then_row() -> None:
    # --- arrange ----------------------
    occ = Occupancy()
    occ.add(2, 3)
    occ.add(0, 5)
    occ.add(2, 1)
    occ.add(0, 1)

    # --- act --------------------------
    points = list(occ)

    # --- assert -----------------------
    assert points == [(0, 1), (0, 5), (2, 1), (2, 3)]


def test_iter_on_empty_occupancy_yields_nothing() -> None:
    # --- arrange / act ----------------
    points = list(Occupancy())

    # --- assert -----------------------
    assert points == []
