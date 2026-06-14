"""Tests for `DarkTheme` — One Dark-inspired palette overrides + render smoke."""

from gitsvg._shared.value_types import BranchLineStyle, Orientation
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.state import apply_ops
from gitsvg.theme.themes import DarkTheme
from tests._jsonl import build_jsonl


# ==================================================================================================
#  Resolved field values
# ==================================================================================================
def test_dark_theme_build_resolves_overridden_palette_fields() -> None:
    """`DarkTheme.build({})` resolves every overridden color field to its dark-theme value."""
    # --- arrange / act ----------------
    theme = DarkTheme.build({})

    # --- assert -----------------------
    assert theme.background_color == "#282c34"
    assert theme.colors == {
        "main": "#abb2bf",
        "branch1": "#98c379",
        "branch2": "#61afef",
        "branch3": "#e06c75",
        "branch4": "#c678dd",
    }
    assert theme.label_color == "#abb2bf"
    assert theme.hash_color == "#7f848e"
    assert theme.branch_guide_color == "#3e4451"
    assert theme.commit_stroke_color == "#282c34"


def test_dark_theme_inherits_non_color_defaults() -> None:
    """`DarkTheme` only overrides color-bearing resolvers — geometry,
    spacing, and typography inherit unchanged from `DefaultTheme`."""
    # --- arrange / act ----------------
    theme = DarkTheme.build({})

    # --- assert -----------------------
    assert theme.orientation == Orientation.BT
    assert theme.branch_spacing == 100
    assert theme.commit_spacing == 50
    assert theme.label_font_size == 11
    assert theme.commit_radius == 5
    assert theme.commit_stroke_width == 1.5
    assert theme.default_branch_color_cycle == ["branch1", "branch2", "branch3", "branch4"]
    assert theme.branch_line_style is BranchLineStyle.BEZIER  # inherits the default bezier connector


def test_dark_theme_build_with_user_overrides_layers_on_palette() -> None:
    """User overrides via `user_set` apply on top of `DarkTheme`'s resolved defaults."""
    # --- arrange / act ----------------
    theme = DarkTheme.build({"background_color": "#000000", "label_font_size": 14})

    # --- assert -----------------------
    assert theme.background_color == "#000000"  # user override wins
    assert theme.label_font_size == 14  # user override wins
    assert theme.colors["main"] == "#abb2bf"  # dark default for untouched field


# ==================================================================================================
#  Cascade — `{name: "dark"}` selects DarkTheme through the apply pass
# ==================================================================================================
def test_theme_op_name_dark_resolves_through_apply() -> None:
    """A `theme:` op with `name: "dark"` ends up resolving the diagram through `DarkTheme`."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(build_jsonl({"op": "theme", "name": "dark"}), file="x.jsonl")
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.background_color == "#282c34"
    assert theme.colors["branch1"] == "#98c379"


def test_dark_then_user_field_layers_on_top() -> None:
    """`{name: dark}` then a separate `theme:` op with an explicit field
    layers the field on top of dark's resolved defaults."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(
        build_jsonl({"op": "theme", "name": "dark"}, {"op": "theme", "background_color": "#101010"}), file="x.jsonl"
    )
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.background_color == "#101010"  # later user override wins
    assert theme.label_color == "#abb2bf"  # dark default for untouched field


def test_keep_prior_overrides_true_preserves_user_fields_into_dark() -> None:
    """`{name: dark, keep_prior_overrides: true}` keeps prior user fields
    instead of wiping them — dark's defaults apply only to untouched fields."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(
        build_jsonl(
            {"op": "theme", "label_font_size": 14}, {"op": "theme", "name": "dark", "keep_prior_overrides": True}
        ),
        file="x.jsonl",
    )
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.label_font_size == 14  # prior user override preserved
    assert theme.background_color == "#282c34"  # dark default for untouched field


# ==================================================================================================
#  Render smoke — output SVG carries the dark palette
# ==================================================================================================
def test_dark_theme_renders_with_expected_palette_colors() -> None:
    """A small diagram rendered through `DarkTheme` produces an SVG
    that contains every palette color the dark theme defines."""
    # --- arrange ----------------------
    source = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "first"},
        {"op": "branch", "name": "feat", "from_branch": "main"},
        {"op": "commit", "branch": "feat", "id": "c2", "msg": "feature"},
        {"op": "theme", "name": "dark"},
    )

    # --- act --------------------------
    parsed, report = parse_jsonl_text(source, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    _, renderer_settings = theme.split()
    layout = compute_layout(state)
    svg = render(layout, renderer_settings).as_svg()

    # --- assert -----------------------
    assert report.is_clean()
    # Dark canvas background.
    assert "#282c34" in svg
    # Main branch palette color appears.
    assert "#abb2bf" in svg
    # Feature branch picks the first cycle color.
    assert "#98c379" in svg
