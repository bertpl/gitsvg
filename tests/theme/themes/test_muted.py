"""Tests for `MutedTheme` — the pre-refresh default look, preserved as a named theme.

Covers the two halves of the refresh: that the package `default` now
resolves to the refreshed values (saturated palette, bezier connectors,
checkmark merge dots), and that `muted` pins exactly those three fields
back so it reproduces the pre-refresh default everywhere else.
"""

from gitsvg._value_types import BranchLineStyle, MergeCommitStyle, Orientation
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import DEFAULT_THEME
from gitsvg.theme.themes import MutedTheme

# The three fields the refresh changed, with their pre-refresh values.
_PRE_REFRESH_PALETTE = {
    "main": "#5c6370",
    "branch1": "#6a9f8d",
    "branch2": "#7b8fb2",
    "branch3": "#b07b8f",
    "branch4": "#9b8fb2",
}
_REFRESHED_PALETTE = {
    "main": "#4a4f5a",
    "branch1": "#56b393",
    "branch2": "#6b8bc2",
    "branch3": "#c06b8b",
    "branch4": "#977fc2",
}


# ==================================================================================================
#  Refreshed default carries the new vocabulary
# ==================================================================================================
def test_default_theme_uses_refreshed_palette_and_styles() -> None:
    """The package default resolves to the saturated palette, bezier connectors, and checkmark merge dots."""
    # --- arrange / act ----------------
    theme = DEFAULT_THEME

    # --- assert -----------------------
    assert theme.colors == _REFRESHED_PALETTE
    assert theme.branch_line_style == BranchLineStyle.BEZIER
    assert theme.merge_commit_style == MergeCommitStyle.CHECKMARK


# ==================================================================================================
#  Muted pins the three refreshed fields back
# ==================================================================================================
def test_muted_theme_resolves_pre_refresh_fields() -> None:
    """`MutedTheme.build({})` resolves the three refreshed fields back to their pre-refresh values."""
    # --- arrange / act ----------------
    theme = MutedTheme.build({})

    # --- assert -----------------------
    assert theme.colors == _PRE_REFRESH_PALETTE
    assert theme.branch_line_style == BranchLineStyle.ROUNDED
    assert theme.merge_commit_style == MergeCommitStyle.CIRCLE


def test_muted_theme_matches_default_on_every_other_field() -> None:
    """`muted` differs from the refreshed default only on the three refreshed fields.

    This is the preserved-look guarantee: `theme: {"name": "muted"}`
    reproduces the pre-refresh default appearance, so anything outside
    the refresh diff must resolve identically between the two themes."""
    # --- arrange / act ----------------
    muted = MutedTheme.build({}).model_dump()
    default = DEFAULT_THEME.model_dump()
    # `muted` pins three resolvers; any field it diverges from the default
    # on must lie within that set. All three genuinely differ now: muted
    # keeps the pre-refresh palette, `rounded` connectors, and circle merge
    # dots, against the default's saturated palette, `bezier`, and checkmark.
    pinned = {"colors", "branch_line_style", "merge_commit_style"}

    # --- assert -----------------------
    differing = {key for key in default if muted[key] != default[key]}
    assert differing == pinned


def test_muted_theme_inherits_non_refresh_defaults() -> None:
    """`MutedTheme` only overrides the three refreshed resolvers — geometry,
    spacing, and typography inherit unchanged from `DefaultTheme`."""
    # --- arrange / act ----------------
    theme = MutedTheme.build({})

    # --- assert -----------------------
    assert theme.orientation == Orientation.BT
    assert theme.branch_spacing == 100
    assert theme.commit_spacing == 50
    assert theme.label_font_size == 11
    assert theme.commit_radius == 5


# ==================================================================================================
#  Cascade — `{name: "muted"}` selects MutedTheme through the apply pass
# ==================================================================================================
def test_theme_op_name_muted_resolves_through_apply() -> None:
    """A `theme:` op with `name: "muted"` resolves the diagram through `MutedTheme`."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text('{"op": "theme", "name": "muted"}\n', file="x.jsonl")
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.colors["main"] == "#5c6370"
    assert theme.branch_line_style == BranchLineStyle.ROUNDED
    assert theme.merge_commit_style == MergeCommitStyle.CIRCLE
