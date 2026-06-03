"""Unit tests for the `is_color_visible` color-string predicate."""

import pytest

from gitsvg._shared.color import is_color_visible


@pytest.mark.parametrize(
    ("color", "expected"),
    [
        (None, False),  # unset
        ("#fff", True),  # 3-digit, opaque
        ("#ffffff", True),  # 6-digit, opaque
        ("#abc", True),
        ("#0000ff", True),
        ("#ffff", True),  # 4-digit, alpha f → opaque
        ("#ffffffff", True),  # 8-digit, alpha ff → opaque
        ("#00000022", True),  # 8-digit, low but non-zero alpha
        ("#fff8", True),  # 4-digit, mid alpha
        ("#fff0", False),  # 4-digit, alpha 0 → transparent
        ("#ffffff00", False),  # 8-digit, alpha 00 → transparent
        ("#00000000", False),  # 8-digit, fully transparent
    ],
)
def test_is_color_visible(color: str | None, expected: bool) -> None:
    # --- arrange / act / assert -------
    assert is_color_visible(color) is expected
