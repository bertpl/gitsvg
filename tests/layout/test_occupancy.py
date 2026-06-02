"""Tests for `gitsvg.layout._occupancy.Occupancy`.

Public API only. Storage shape is private and never asserted on.
"""

import pytest

from gitsvg.layout._occupancy import Occupancy


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
