"""Tests for the renderer-side `Theme` and `build_theme(state)` adapter."""

from gitsvg._theme import DEFAULT_THEME, Theme
from gitsvg.parse import parse_jsonl_text
from gitsvg.render._theme import build_theme
from gitsvg.state import apply_ops


def _state_from(text: str):
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    return apply_ops(parsed, report)


# ==================================================================================================
#  Defaults
# ==================================================================================================
def test_default_theme_values_pin_the_byte_identical_baseline() -> None:
    """The default theme's values match the rendered-SVG baseline the
    package ships against — byte-identical output depends on these
    constants not drifting."""
    # --- arrange / act / assert -------
    assert DEFAULT_THEME.branch_spacing == 100
    assert DEFAULT_THEME.commit_spacing == 50
    assert DEFAULT_THEME.margin_branch_axis_lower == 100
    assert DEFAULT_THEME.margin_branch_axis_upper == 100
    assert DEFAULT_THEME.margin_commit_axis_lower == 25
    assert DEFAULT_THEME.margin_commit_axis_upper == 25
    assert DEFAULT_THEME.branch_line_width == 2
    assert DEFAULT_THEME.commit_radius == 5
    assert DEFAULT_THEME.commit_stroke_width == 1.5
    assert DEFAULT_THEME.highlight_radius == 7
    assert DEFAULT_THEME.arc_corner_radius == 20
    assert DEFAULT_THEME.label_offset == 12
    assert DEFAULT_THEME.branch_guide_width == 0.7
    assert DEFAULT_THEME.branch_guide_dash == "4,4"
    assert DEFAULT_THEME.label_font_size == 11
    assert DEFAULT_THEME.branch_label_font_size == 11
    assert DEFAULT_THEME.hash_font_size == 9
    assert DEFAULT_THEME.branch_name_pill_offset_commit_axis_in_rows == -0.5
    assert DEFAULT_THEME.branch_name_pill_offset_branch_axis_in_lanes == 0.0
    assert DEFAULT_THEME.pull_request_dash == "6,4"
    assert DEFAULT_THEME.pull_request_pill_offset_commit_axis_in_rows == 0.5
    assert DEFAULT_THEME.pull_request_pill_offset_branch_axis_in_lanes == 0.0
    assert DEFAULT_THEME.background_color is None
    assert DEFAULT_THEME.colors["main"] == "#5c6370"
    assert DEFAULT_THEME.default_branch_color_cycle == ["branch1", "branch2", "branch3", "branch4"]


def test_default_theme_has_no_branch_color_overrides() -> None:
    # --- assert -----------------------
    assert DEFAULT_THEME.branch_color_overrides == {}


# ==================================================================================================
#  build_theme — branch colour overrides keyed by id, not name
# ==================================================================================================
def test_build_theme_collects_branch_color_overrides_keyed_by_id() -> None:
    """When a `branch` op carries an explicit `color:` field, the override
    lands on `theme.branch_color_overrides[branch.id]`."""
    # --- arrange ----------------------
    state = _state_from('{"op": "branch", "name": "main", "color": "#abcdef"}\n')

    # --- act --------------------------
    theme = build_theme(state)

    # --- assert -----------------------
    main_id = state.branches["main"].id
    assert theme.branch_color_overrides[main_id] == "#abcdef"


def test_build_theme_omits_branches_without_color_overrides() -> None:
    # --- arrange ----------------------
    state = _state_from('{"op": "branch", "name": "main"}\n')

    # --- act --------------------------
    theme = build_theme(state)

    # --- assert -----------------------
    assert theme.branch_color_overrides == {}


def test_build_theme_keys_by_id_distinguishes_removed_and_redeclared_branch() -> None:
    """A removed branch and a fresh branch with the same name get different ids;
    only the live branch's override survives in the resolved theme."""
    # --- arrange ----------------------
    state = _state_from(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "color": "#111111"}\n'
        '{"op": "remove", "branches": ["feat"]}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "color": "#222222"}\n'
    )

    # --- act --------------------------
    theme = build_theme(state)

    # --- assert -----------------------
    # Only the live `feat` is in state.branches; its id maps to "#222222".
    live_feat = state.branches["feat"]
    assert theme.branch_color_overrides[live_feat.id] == "#222222"
    # No stale entry pointing at "#111111" survives.
    assert "#111111" not in theme.branch_color_overrides.values()


# ==================================================================================================
#  build_theme — defaults
# ==================================================================================================
def test_build_theme_with_no_theme_op_returns_defaults() -> None:
    """No `theme:` op → resolved theme matches `DEFAULT_THEME` field-for-field."""
    # --- arrange ----------------------
    state = _state_from('{"op": "branch", "name": "main"}\n')

    # --- act --------------------------
    theme = build_theme(state)

    # --- assert -----------------------
    assert theme.branch_spacing == DEFAULT_THEME.branch_spacing
    assert theme.commit_spacing == DEFAULT_THEME.commit_spacing
    assert theme.margin_branch_axis_lower == DEFAULT_THEME.margin_branch_axis_lower
    assert theme.margin_branch_axis_upper == DEFAULT_THEME.margin_branch_axis_upper
    assert theme.background_color is None


def test_build_theme_returns_fresh_instance_per_call() -> None:
    """Mutating the returned theme must not affect `DEFAULT_THEME`."""
    # --- arrange ----------------------
    state = _state_from('{"op": "branch", "name": "main"}\n')

    # --- act --------------------------
    theme = build_theme(state)
    theme.branch_spacing = 1234

    # --- assert -----------------------
    assert DEFAULT_THEME.branch_spacing == 100


def test_theme_dataclass_is_constructible_with_explicit_values() -> None:
    """Sanity check: nothing prevents constructing a custom theme directly."""
    # --- arrange / act ----------------
    theme = Theme(branch_spacing=120, background_color="#222222")

    # --- assert -----------------------
    assert theme.branch_spacing == 120
    assert theme.background_color == "#222222"


def test_build_theme_starts_from_state_theme_not_default() -> None:
    """When a `theme:` op has mutated `state.theme`, `build_theme` uses
    the mutated values — not `DEFAULT_THEME` — as its base."""
    # --- arrange ----------------------
    state = _state_from('{"op": "theme", "background_color": "#deadbe"}\n{"op": "branch", "name": "main"}\n')

    # --- act --------------------------
    theme = build_theme(state)

    # --- assert -----------------------
    assert theme.background_color == "#deadbe"
    # DEFAULT_THEME is unchanged.
    assert DEFAULT_THEME.background_color is None


def test_build_theme_does_not_alias_state_theme() -> None:
    """The returned `Theme` is a fresh copy — mutating it must not bleed
    back into `state.theme`."""
    # --- arrange ----------------------
    state = _state_from('{"op": "theme", "background_color": "#abcdef"}\n{"op": "branch", "name": "main"}\n')

    # --- act --------------------------
    theme = build_theme(state)
    theme.background_color = "#000000"

    # --- assert -----------------------
    assert state.theme.background_color == "#abcdef"
    # Unspecified fields fall back to defaults.
    assert theme.commit_spacing == DEFAULT_THEME.commit_spacing
