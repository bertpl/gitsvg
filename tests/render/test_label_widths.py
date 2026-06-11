"""Tests for the pill/label sizing helpers in `_label_widths.py`."""

from gitsvg.render._label_widths import pill_height
from gitsvg.theme import DEFAULT_THEME

_, _RENDERER_SETTINGS = DEFAULT_THEME.split()


def test_pill_height_is_font_size_plus_vertical_padding() -> None:
    # --- act / assert -----------------
    rs = _RENDERER_SETTINGS
    assert pill_height(rs) == rs.branch_label_font_size + rs.pill_padding_y
