"""Tests for the `Theme` Pydantic model and `DEFAULT_THEME` baseline values."""

from gitsvg.theme import DEFAULT_THEME, DefaultTheme, Orientation, Theme


# ==================================================================================================
#  Defaults
# ==================================================================================================
def test_default_theme_values_pin_the_byte_identical_baseline() -> None:
    """`DEFAULT_THEME` is the fully-resolved default theme — `DefaultTheme.build({})`.

    Every field carries its resolved value; orientation-dependent
    fields resolve under the default orientation (`bt`). Byte-identical
    SVG output across the shipped examples depends on these values not
    drifting.
    """
    # --- arrange / act / assert -------
    assert DEFAULT_THEME.orientation == Orientation.BT
    # Orientation-resolved fields (under default `bt`).
    assert DEFAULT_THEME.branch_spacing == 100
    assert DEFAULT_THEME.commit_spacing == 50
    assert DEFAULT_THEME.margin_left == 100
    assert DEFAULT_THEME.margin_right == 100
    assert DEFAULT_THEME.margin_bottom == 25
    assert DEFAULT_THEME.margin_top == 25
    # Orientation-invariant constants.
    assert DEFAULT_THEME.branch_line_width == 2
    assert DEFAULT_THEME.commit_radius == 5
    assert DEFAULT_THEME.commit_stroke_width == 1.5
    assert DEFAULT_THEME.highlight_radius == 7
    assert DEFAULT_THEME.arc_corner_radius == 20  # ratio property, 0.4 * min(100,50)
    assert DEFAULT_THEME.label_offset == 12  # ratio property, 0.12 * 100
    assert DEFAULT_THEME.branch_guide_width == 0.7
    assert DEFAULT_THEME.branch_guide_dash == "4,4"
    assert DEFAULT_THEME.label_font_size == 11
    assert DEFAULT_THEME.branch_label_font_size == 11
    assert DEFAULT_THEME.hash_font_size == 9
    # Pill offsets under default orientation.
    assert DEFAULT_THEME.branch_name_pill_offset_commit_axis_in_rows == -0.5
    assert DEFAULT_THEME.branch_name_pill_offset_branch_axis_in_lanes == 0.0
    assert DEFAULT_THEME.pull_request_dash == "2,6"
    assert DEFAULT_THEME.pull_request_pill_offset_commit_axis_in_rows == -0.5
    assert DEFAULT_THEME.pull_request_pill_offset_branch_axis_in_lanes == 0.0
    assert DEFAULT_THEME.background_color is None
    assert DEFAULT_THEME.colors["main"] == "#5c6370"
    assert DEFAULT_THEME.default_branch_color_cycle == ["branch1", "branch2", "branch3", "branch4"]


def test_default_theme_has_no_branch_color_overrides() -> None:
    # --- assert -----------------------
    assert DEFAULT_THEME.branch_color_overrides == {}


def test_theme_constructible_with_explicit_values() -> None:
    """Sanity check: `Theme` accepts explicit field values at construction.

    Useful for tests that want a partial theme without going through
    `build()`. Note that fields left at the default (`None`) are
    *unresolved* — for a fully-populated theme go through
    `DefaultTheme.build({...})`.
    """
    # --- arrange / act ----------------
    theme = Theme(branch_spacing=120, background_color="#222222")

    # --- assert -----------------------
    assert theme.branch_spacing == 120
    assert theme.background_color == "#222222"
    # Other fields remain at the unresolved sentinel.
    assert theme.commit_spacing is None


def test_default_theme_build_with_overrides() -> None:
    """`DefaultTheme.build({...})` resolves a theme with user overrides applied."""
    # --- arrange / act ----------------
    theme = DefaultTheme.build({"branch_spacing": 120, "background_color": "#222222"})

    # --- assert -----------------------
    assert theme.branch_spacing == 120  # explicit override
    assert theme.background_color == "#222222"  # explicit override
    assert theme.commit_spacing == 50  # default (resolved under `bt`)
    assert theme.orientation == Orientation.BT  # default
