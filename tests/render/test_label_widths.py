"""Tests for the pill/label sizing helpers in `_label_widths.py`."""

from gitsvg.render._label_widths import pill_height
from gitsvg.theme import DEFAULT_THEME


def test_pill_height_is_font_size_plus_vertical_padding() -> None:
    # --- act / assert -----------------
    assert pill_height(DEFAULT_THEME) == DEFAULT_THEME.branch_label_font_size + DEFAULT_THEME.pill_padding_y
