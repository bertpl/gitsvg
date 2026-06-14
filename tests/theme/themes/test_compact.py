"""Tests for `CompactTheme` — denser spacings + smaller fonts + adjusted pill offsets."""

from gitsvg._shared.value_types import BranchLineStyle, MergeCommitStyle, Orientation
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_text
from gitsvg.render import render
from gitsvg.state import apply_ops
from gitsvg.theme.themes import CompactTheme
from tests._jsonl import build_jsonl


# ==================================================================================================
#  Resolved field values
# ==================================================================================================
def test_compact_theme_build_resolves_overridden_metrics_vertical() -> None:
    """`CompactTheme.build({})` under the default vertical orientation resolves
    every overridden metric to its compact value."""
    # --- arrange / act ----------------
    theme = CompactTheme.build({})

    # --- assert -----------------------
    assert theme.orientation == Orientation.BT
    assert theme.branch_spacing == 75
    assert theme.commit_spacing == 35
    assert theme.label_font_size == 9.5
    assert theme.branch_label_font_size == 10
    assert theme.hash_font_size == 8
    assert theme.branch_name_pill_offset_commit_axis_in_rows == -0.65
    assert theme.pull_request_pill_offset_commit_axis_in_rows == -0.35


def test_compact_theme_build_resolves_overridden_metrics_horizontal() -> None:
    """Horizontal orientations get their own spacings; pill offsets inherit `DefaultTheme`."""
    # --- arrange / act ----------------
    theme = CompactTheme.build({"orientation": Orientation.LR})

    # --- assert -----------------------
    assert theme.branch_spacing == 55
    assert theme.commit_spacing == 55
    # Pill offsets: horizontal values inherited from `DefaultTheme` (no compact override).
    assert theme.branch_name_pill_offset_commit_axis_in_rows == -0.25
    assert theme.pull_request_pill_offset_commit_axis_in_rows == 0.0


def test_compact_theme_inherits_default_palette() -> None:
    """`CompactTheme` inherits the refreshed default palette unchanged — it varies metrics, not color."""
    # --- arrange / act ----------------
    theme = CompactTheme.build({})

    # --- assert -----------------------
    assert theme.background_color is None
    assert theme.colors["main"] == "#4a4f5a"
    assert theme.label_color == "#383838"
    assert theme.commit_stroke_color == "white"


def test_compact_theme_packs_tightly_and_inherits_bezier_checkmark() -> None:
    """`CompactTheme` turns on `auto_lane_change` with zero merge-lane clearance
    for the tightest packing, while inheriting the default's bezier connectors
    and checkmark merge dots."""
    # --- arrange / act ----------------
    theme = CompactTheme.build({})

    # --- assert -----------------------
    assert theme.auto_lane_change is True
    assert theme.merge_lane_clearance == 0
    assert theme.branch_line_style is BranchLineStyle.BEZIER  # inherited from DefaultTheme
    assert theme.merge_commit_style is MergeCommitStyle.CHECKMARK


def test_compact_theme_build_with_user_overrides_layers_on_metrics() -> None:
    """User overrides via `user_set` apply on top of `CompactTheme`'s resolved defaults."""
    # --- arrange / act ----------------
    theme = CompactTheme.build({"branch_spacing": 90, "label_font_size": 12})

    # --- assert -----------------------
    assert theme.branch_spacing == 90  # user override wins
    assert theme.label_font_size == 12  # user override wins
    assert theme.commit_spacing == 35  # compact default for untouched field


# ==================================================================================================
#  Cascade — `{name: "compact"}` selects CompactTheme through the apply pass
# ==================================================================================================
def test_theme_op_name_compact_resolves_through_apply() -> None:
    """A `theme:` op with `name: "compact"` ends up resolving the diagram through `CompactTheme`."""
    # --- arrange / act ----------------
    parsed, report = parse_jsonl_text(build_jsonl({"op": "theme", "name": "compact"}), file="x.jsonl")
    _, theme = apply_ops(parsed, report)

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.branch_spacing == 75
    assert theme.label_font_size == 9.5


# ==================================================================================================
#  Render smoke — output SVG carries the compact font size
# ==================================================================================================
def test_compact_theme_renders_with_expected_font_size() -> None:
    """A small diagram rendered through `CompactTheme` produces an SVG
    that contains the compact label font-size string."""
    # --- arrange ----------------------
    source = build_jsonl(
        {"op": "branch", "name": "main"},
        {"op": "commit", "branch": "main", "id": "c1", "msg": "first"},
        {"op": "theme", "name": "compact"},
    )

    # --- act --------------------------
    parsed, report = parse_jsonl_text(source, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    _, renderer_settings = theme.split()
    layout = compute_layout(state)
    svg = render(layout, renderer_settings).as_svg()

    # --- assert -----------------------
    assert report.is_clean()
    # 9.5 is the half-step compact label size; renders as the literal "9.5".
    assert 'font-size="9.5"' in svg
