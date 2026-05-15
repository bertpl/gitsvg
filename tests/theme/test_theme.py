"""Tests for the `Theme` dataclass and `DEFAULT_THEME` baseline values."""

import copy

from gitsvg.theme import DEFAULT_THEME, Theme, resolve_defaults


def _resolved_default() -> Theme:
    """Return a fresh resolved copy of `DEFAULT_THEME` for property-on-default assertions."""
    theme = copy.deepcopy(DEFAULT_THEME)
    resolve_defaults(theme)
    return theme


# ==================================================================================================
#  Defaults
# ==================================================================================================
def test_default_theme_values_pin_the_byte_identical_baseline() -> None:
    """The default theme's values match the rendered-SVG baseline the
    package ships against — byte-identical output depends on these
    constants not drifting.

    Orientation-resolved fields (spacings, margins, pill offsets) are
    `None` on the unresolved `DEFAULT_THEME`; the resolver fills them
    per orientation at end of state stage. The resolver tests cover
    those values; this test covers the non-resolved fields and the
    sentinel-None status of the resolved ones.
    """
    # --- arrange / act / assert -------
    assert DEFAULT_THEME.orientation == "bt"
    # Orientation-resolved fields: sentinel `None` on DEFAULT_THEME.
    assert DEFAULT_THEME.branch_spacing is None
    assert DEFAULT_THEME.commit_spacing is None
    assert DEFAULT_THEME.margin_left is None
    assert DEFAULT_THEME.margin_right is None
    assert DEFAULT_THEME.margin_bottom is None
    assert DEFAULT_THEME.margin_top is None
    assert DEFAULT_THEME.branch_line_width == 2
    assert DEFAULT_THEME.commit_radius == 5
    assert DEFAULT_THEME.commit_stroke_width == 1.5
    assert DEFAULT_THEME.highlight_radius == 7
    # Ratio-anchored properties: tested on a resolved copy because the
    # property accessor multiplies by spacings (None on unresolved).
    assert _resolved_default().arc_corner_radius == 20
    assert _resolved_default().label_offset == 12
    assert DEFAULT_THEME.branch_guide_width == 0.7
    assert DEFAULT_THEME.branch_guide_dash == "4,4"
    assert DEFAULT_THEME.label_font_size == 11
    assert DEFAULT_THEME.branch_label_font_size == 11
    assert DEFAULT_THEME.hash_font_size == 9
    # Pill offsets are orientation-resolved — sentinel `None` until resolution.
    assert DEFAULT_THEME.branch_name_pill_offset_commit_axis_in_rows is None
    assert DEFAULT_THEME.branch_name_pill_offset_branch_axis_in_lanes is None
    assert DEFAULT_THEME.pull_request_dash == "2,6"
    assert DEFAULT_THEME.pull_request_pill_offset_commit_axis_in_rows is None
    assert DEFAULT_THEME.pull_request_pill_offset_branch_axis_in_lanes is None
    assert DEFAULT_THEME.background_color is None
    assert DEFAULT_THEME.colors["main"] == "#5c6370"
    assert DEFAULT_THEME.default_branch_color_cycle == ["branch1", "branch2", "branch3", "branch4"]


def test_default_theme_has_no_branch_color_overrides() -> None:
    # --- assert -----------------------
    assert DEFAULT_THEME.branch_color_overrides == {}


def test_theme_dataclass_is_constructible_with_explicit_values() -> None:
    """Sanity check: nothing prevents constructing a custom theme directly."""
    # --- arrange / act ----------------
    theme = Theme(branch_spacing=120, background_color="#222222")

    # --- assert -----------------------
    assert theme.branch_spacing == 120
    assert theme.background_color == "#222222"
