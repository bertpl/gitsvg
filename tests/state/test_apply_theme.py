"""Tests for `apply_theme_op` — cascade rule, named-theme replacement, validation."""

from gitsvg._theme import DEFAULT_THEME
from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops


def _state_from(text: str):
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state = apply_ops(parsed, report)
    return state, report


# ==================================================================================================
#  Cascade — explicit-fields-only patch
# ==================================================================================================
def test_explicit_field_override_assigns_only_that_field() -> None:
    # --- arrange / act ----------------
    state, report = _state_from('{"op": "theme", "background_color": "#abcdef"}\n')

    # --- assert -----------------------
    assert report.is_clean()
    assert state.theme.background_color == "#abcdef"
    # Other fields keep their defaults.
    assert state.theme.branch_spacing == DEFAULT_THEME.branch_spacing
    assert state.theme.commit_spacing == DEFAULT_THEME.commit_spacing


def test_multiple_explicit_fields_in_one_op_all_apply() -> None:
    # --- arrange / act ----------------
    state, report = _state_from(
        '{"op": "theme", "branch_spacing": 80, "background_color": "#101010", "label_font_size": 13}\n'
    )

    # --- assert -----------------------
    assert report.is_clean()
    assert state.theme.branch_spacing == 80
    assert state.theme.background_color == "#101010"
    assert state.theme.label_font_size == 13
    # Untouched field stays at the default.
    assert state.theme.commit_spacing == DEFAULT_THEME.commit_spacing


def test_sequential_explicit_overrides_accumulate() -> None:
    # --- arrange / act ----------------
    state, report = _state_from(
        '{"op": "theme", "background_color": "#111111"}\n{"op": "theme", "label_font_size": 17}\n'
    )

    # --- assert -----------------------
    assert report.is_clean()
    # Both fields stuck — second op didn't reset the first.
    assert state.theme.background_color == "#111111"
    assert state.theme.label_font_size == 17


def test_second_explicit_op_overwrites_same_field() -> None:
    # --- arrange / act ----------------
    state, report = _state_from(
        '{"op": "theme", "background_color": "#aaaaaa"}\n{"op": "theme", "background_color": "#bbbbbb"}\n'
    )

    # --- assert -----------------------
    assert report.is_clean()
    assert state.theme.background_color == "#bbbbbb"


# ==================================================================================================
#  Cascade — named theme replaces all fields
# ==================================================================================================
def test_named_default_theme_keeps_defaults() -> None:
    # --- arrange / act ----------------
    state, report = _state_from('{"op": "theme", "name": "default"}\n')

    # --- assert -----------------------
    assert report.is_clean()
    assert state.theme.branch_spacing == DEFAULT_THEME.branch_spacing
    assert state.theme.background_color == DEFAULT_THEME.background_color


def test_named_theme_replaces_prior_explicit_overrides() -> None:
    """A named-theme op resets every field — explicit overrides from
    earlier ops do not survive."""
    # --- arrange / act ----------------
    state, report = _state_from('{"op": "theme", "background_color": "#deadbe"}\n{"op": "theme", "name": "default"}\n')

    # --- assert -----------------------
    assert report.is_clean()
    # The named-theme reset reverted background_color to the default's None.
    assert state.theme.background_color == DEFAULT_THEME.background_color


# ==================================================================================================
#  Cascade — mixed op (name + explicit fields)
# ==================================================================================================
def test_mixed_op_applies_name_first_then_explicit() -> None:
    """In a single op carrying both `name` and explicit fields, the
    name replaces everything first, then the explicit fields override
    on top."""
    # --- arrange / act ----------------
    state, report = _state_from(
        '{"op": "theme", "background_color": "#111111"}\n{"op": "theme", "name": "default", "label_font_size": 17}\n'
    )

    # --- assert -----------------------
    assert report.is_clean()
    # background_color reset by the named-theme replace step.
    assert state.theme.background_color == DEFAULT_THEME.background_color
    # label_font_size overridden on top.
    assert state.theme.label_font_size == 17


def test_mixed_then_partial_sequence() -> None:
    """Mixed op replaces + overrides; a later partial op patches one more field."""
    # --- arrange / act ----------------
    state, report = _state_from(
        '{"op": "theme", "name": "default", "label_font_size": 17}\n{"op": "theme", "branch_spacing": 80}\n'
    )

    # --- assert -----------------------
    assert report.is_clean()
    assert state.theme.label_font_size == 17  # from the mixed op
    assert state.theme.branch_spacing == 80  # from the partial op
    assert state.theme.commit_spacing == DEFAULT_THEME.commit_spacing  # never touched


# ==================================================================================================
#  Cascade — palette (`colors` dict) override
# ==================================================================================================
def test_colors_palette_override_replaces_palette_wholesale() -> None:
    """The `colors` field replaces the entire branch palette dict —
    keys not present in the new dict are not preserved."""
    # --- arrange / act ----------------
    state, report = _state_from('{"op": "theme", "colors": {"main": "#d62728", "branch1": "#1f77b4"}}\n')

    # --- assert -----------------------
    assert report.is_clean()
    assert state.theme.colors == {"main": "#d62728", "branch1": "#1f77b4"}


def test_colors_override_does_not_alias_op_dict() -> None:
    """Mutating `state.theme.colors` after apply must not leak back into
    the parsed op (defensive — pydantic shouldn't be re-applied, but the
    deep-copy keeps the invariant clean)."""
    # --- arrange / act ----------------
    state, _ = _state_from('{"op": "theme", "colors": {"main": "#d62728"}}\n')
    state.theme.colors["main"] = "#000000"
    state2, _ = _state_from('{"op": "theme", "colors": {"main": "#d62728"}}\n')

    # --- assert -----------------------
    # Each state's theme.colors is independent.
    assert state2.theme.colors == {"main": "#d62728"}


# ==================================================================================================
#  Validation
# ==================================================================================================
def test_empty_op_emits_e217() -> None:
    # --- arrange / act ----------------
    state, report = _state_from('{"op": "theme"}\n')

    # --- assert -----------------------
    assert not report.is_clean()
    codes = [e.code for e in report.errors]
    assert "E217" in codes
    # State theme is untouched — still all defaults.
    assert state.theme.background_color == DEFAULT_THEME.background_color


def test_unknown_named_theme_emits_e216() -> None:
    # --- arrange / act ----------------
    state, report = _state_from('{"op": "theme", "name": "midnight"}\n')

    # --- assert -----------------------
    assert not report.is_clean()
    codes = [e.code for e in report.errors]
    assert "E216" in codes
    # State theme is untouched — the error short-circuited the apply.
    assert state.theme.background_color == DEFAULT_THEME.background_color


def test_unknown_named_theme_does_not_apply_explicit_fields() -> None:
    """When `name` is invalid, the *entire* op is rejected — explicit
    overrides on the same op also do not apply."""
    # --- arrange / act ----------------
    state, report = _state_from('{"op": "theme", "name": "midnight", "background_color": "#abcdef"}\n')

    # --- assert -----------------------
    assert not report.is_clean()
    assert state.theme.background_color == DEFAULT_THEME.background_color


# ==================================================================================================
#  Independence between state instances
# ==================================================================================================
def test_state_theme_mutation_does_not_leak_into_default() -> None:
    """Each state starts with its own deep copy of DEFAULT_THEME — mutating
    one diagram's theme must not affect another."""
    # --- arrange / act ----------------
    state, _ = _state_from('{"op": "theme", "background_color": "#123456"}\n')

    # --- assert -----------------------
    assert state.theme.background_color == "#123456"
    assert DEFAULT_THEME.background_color is None  # untouched


def test_branch_color_overrides_survive_explicit_theme_patch() -> None:
    """A `theme:` op that doesn't mention `branch_color_overrides`
    leaves prior `branch.color` overrides intact in the resolved theme."""
    from gitsvg.render._theme import build_theme

    # --- arrange / act ----------------
    state, report = _state_from(
        '{"op": "branch", "name": "main", "color": "#aabbcc"}\n{"op": "theme", "background_color": "#111111"}\n'
    )

    # --- assert -----------------------
    assert report.is_clean()
    theme = build_theme(state)
    main_id = state.branches["main"].id
    assert theme.branch_color_overrides[main_id] == "#aabbcc"
    assert theme.background_color == "#111111"
