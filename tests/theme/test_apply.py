"""Tests for `apply_theme_op` — cascade rule, named-theme replacement, validation."""

import pytest

from gitsvg.parse import parse_jsonl_text
from gitsvg.state import apply_ops
from gitsvg.theme import DEFAULT_THEME


def _apply(text: str):
    parsed, report = parse_jsonl_text(text, file="x.jsonl")
    state, theme = apply_ops(parsed, report)
    return state, theme, report


# ==================================================================================================
#  Cascade — explicit-fields-only patch
# ==================================================================================================
def test_explicit_field_override_assigns_only_that_field() -> None:
    # --- arrange / act ----------------
    _, theme, report = _apply('{"op": "theme", "background_color": "#abcdef"}\n')

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.background_color == "#abcdef"
    # Other fields keep their defaults.
    assert theme.branch_spacing == DEFAULT_THEME.branch_spacing
    assert theme.commit_spacing == DEFAULT_THEME.commit_spacing


def test_multiple_explicit_fields_in_one_op_all_apply() -> None:
    # --- arrange / act ----------------
    _, theme, report = _apply(
        '{"op": "theme", "branch_spacing": 80, "background_color": "#101010", "label_font_size": 13}\n'
    )

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.branch_spacing == 80
    assert theme.background_color == "#101010"
    assert theme.label_font_size == 13
    # Untouched field stays at the default.
    assert theme.commit_spacing == DEFAULT_THEME.commit_spacing


def test_sequential_explicit_overrides_accumulate() -> None:
    # --- arrange / act ----------------
    _, theme, report = _apply(
        '{"op": "theme", "background_color": "#111111"}\n{"op": "theme", "label_font_size": 17}\n'
    )

    # --- assert -----------------------
    assert report.is_clean()
    # Both fields stuck — second op didn't reset the first.
    assert theme.background_color == "#111111"
    assert theme.label_font_size == 17


def test_second_explicit_op_overwrites_same_field() -> None:
    # --- arrange / act ----------------
    _, theme, report = _apply(
        '{"op": "theme", "background_color": "#aaaaaa"}\n{"op": "theme", "background_color": "#bbbbbb"}\n'
    )

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.background_color == "#bbbbbb"


# ==================================================================================================
#  Cascade — named theme replaces all fields
# ==================================================================================================
def test_named_default_theme_keeps_defaults() -> None:
    # --- arrange / act ----------------
    _, theme, report = _apply('{"op": "theme", "name": "default"}\n')

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.branch_spacing == DEFAULT_THEME.branch_spacing
    assert theme.background_color == DEFAULT_THEME.background_color


def test_named_theme_replaces_prior_explicit_overrides() -> None:
    """A named-theme op resets every field — explicit overrides from
    earlier ops do not survive."""
    # --- arrange / act ----------------
    _, theme, report = _apply('{"op": "theme", "background_color": "#deadbe"}\n{"op": "theme", "name": "default"}\n')

    # --- assert -----------------------
    assert report.is_clean()
    # The named-theme reset reverted background_color to the default's None.
    assert theme.background_color == DEFAULT_THEME.background_color


# ==================================================================================================
#  Cascade — mixed op (name + explicit fields)
# ==================================================================================================
def test_mixed_op_applies_name_first_then_explicit() -> None:
    """In a single op carrying both `name` and explicit fields, the
    name replaces everything first, then the explicit fields override
    on top."""
    # --- arrange / act ----------------
    _, theme, report = _apply(
        '{"op": "theme", "background_color": "#111111"}\n{"op": "theme", "name": "default", "label_font_size": 17}\n'
    )

    # --- assert -----------------------
    assert report.is_clean()
    # background_color reset by the named-theme replace step.
    assert theme.background_color == DEFAULT_THEME.background_color
    # label_font_size overridden on top.
    assert theme.label_font_size == 17


def test_mixed_then_partial_sequence() -> None:
    """Mixed op replaces + overrides; a later partial op patches one more field."""
    # --- arrange / act ----------------
    _, theme, report = _apply(
        '{"op": "theme", "name": "default", "label_font_size": 17}\n{"op": "theme", "branch_spacing": 80}\n'
    )

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.label_font_size == 17  # from the mixed op
    assert theme.branch_spacing == 80  # from the partial op
    assert theme.commit_spacing == DEFAULT_THEME.commit_spacing  # never touched


# ==================================================================================================
#  Cascade — palette (`colors` dict) override
# ==================================================================================================
def test_colors_palette_override_replaces_palette_wholesale() -> None:
    """The `colors` field replaces the entire branch palette dict —
    keys not present in the new dict are not preserved."""
    # --- arrange / act ----------------
    _, theme, report = _apply('{"op": "theme", "colors": {"main": "#d62728", "branch1": "#1f77b4"}}\n')

    # --- assert -----------------------
    assert report.is_clean()
    assert theme.colors == {"main": "#d62728", "branch1": "#1f77b4"}


def test_colors_override_does_not_alias_op_dict() -> None:
    """Mutating a theme's `colors` after apply must not leak back into
    the parsed op (defensive — pydantic shouldn't be re-applied, but the
    deep-copy keeps the invariant clean)."""
    # --- arrange / act ----------------
    _, theme, _ = _apply('{"op": "theme", "colors": {"main": "#d62728"}}\n')
    theme.colors["main"] = "#000000"
    _, theme2, _ = _apply('{"op": "theme", "colors": {"main": "#d62728"}}\n')

    # --- assert -----------------------
    # Each apply pass produces an independent theme.colors.
    assert theme2.colors == {"main": "#d62728"}


# ==================================================================================================
#  Validation
# ==================================================================================================
def test_empty_op_emits_e217() -> None:
    # --- arrange / act ----------------
    _, theme, report = _apply('{"op": "theme"}\n')

    # --- assert -----------------------
    assert not report.is_clean()
    codes = [e.code for e in report.errors]
    assert "E217" in codes
    # Theme is untouched — still all defaults.
    assert theme.background_color == DEFAULT_THEME.background_color


def test_unknown_named_theme_emits_e216() -> None:
    # --- arrange / act ----------------
    _, theme, report = _apply('{"op": "theme", "name": "midnight"}\n')

    # --- assert -----------------------
    assert not report.is_clean()
    codes = [e.code for e in report.errors]
    assert "E216" in codes
    # Theme is untouched — the error short-circuited the apply.
    assert theme.background_color == DEFAULT_THEME.background_color


def test_unknown_named_theme_does_not_apply_explicit_fields() -> None:
    """When `name` is invalid, the *entire* op is rejected — explicit
    overrides on the same op also do not apply."""
    # --- arrange / act ----------------
    _, theme, report = _apply('{"op": "theme", "name": "midnight", "background_color": "#abcdef"}\n')

    # --- assert -----------------------
    assert not report.is_clean()
    assert theme.background_color == DEFAULT_THEME.background_color


# ==================================================================================================
#  Independence between apply passes
# ==================================================================================================
def test_theme_mutation_does_not_leak_into_default() -> None:
    """Each apply pass starts with its own deep copy of DEFAULT_THEME — mutating
    one diagram's theme must not affect another."""
    # --- arrange / act ----------------
    _, theme, _ = _apply('{"op": "theme", "background_color": "#123456"}\n')

    # --- assert -----------------------
    assert theme.background_color == "#123456"
    assert DEFAULT_THEME.background_color is None  # untouched


def test_branch_color_overrides_survive_explicit_theme_patch() -> None:
    """A `theme:` op that doesn't mention `branch_color_overrides`
    leaves prior `branch.color` overrides intact in the resolved theme."""
    # --- arrange / act ----------------
    state, theme, report = _apply(
        '{"op": "branch", "name": "main", "color": "#aabbcc"}\n{"op": "theme", "background_color": "#111111"}\n'
    )

    # --- assert -----------------------
    assert report.is_clean()
    main_id = state.branches["main"].id
    assert theme.branch_color_overrides[main_id] == "#aabbcc"
    assert theme.background_color == "#111111"


# ==================================================================================================
#  Theme-field semantic validation
# ==================================================================================================
@pytest.mark.parametrize("field", ["branch_spacing", "commit_spacing"])
def test_spacing_must_be_positive_emits_e218(field: str) -> None:
    # --- arrange / act ----------------
    _, _, report = _apply(f'{{"op": "theme", "{field}": 0}}\n')

    # --- assert -----------------------
    codes = [e.code for e in report.errors]
    assert codes == ["E218"]
    assert field in report.errors[0].message


def test_spacing_violation_does_not_block_other_fields_in_same_op() -> None:
    """An invalid spacing emits an error but other valid fields still apply."""
    # --- arrange / act ----------------
    _, theme, report = _apply('{"op": "theme", "branch_spacing": 0, "background_color": "#abcdef"}\n')

    # --- assert -----------------------
    assert [e.code for e in report.errors] == ["E218"]
    # Background color from the same op applied; branch_spacing kept its default.
    assert theme.background_color == "#abcdef"
    assert theme.branch_spacing == DEFAULT_THEME.branch_spacing


@pytest.mark.parametrize("field", ["label_font_size", "branch_label_font_size", "hash_font_size"])
def test_font_size_must_be_positive_emits_e219(field: str) -> None:
    # --- arrange / act ----------------
    _, _, report = _apply(f'{{"op": "theme", "{field}": 0}}\n')

    # --- assert -----------------------
    codes = [e.code for e in report.errors]
    assert codes == ["E219"]
    assert field in report.errors[0].message


# ==================================================================================================
#  Branch-colour overrides — written by `apply_branch_op` to `theme.branch_color_overrides`
# ==================================================================================================
def test_branch_op_with_color_writes_override_keyed_by_id() -> None:
    """When a `branch` op carries an explicit `color:` field, the override
    lands on `theme.branch_color_overrides[branch.id]`."""
    # --- arrange / act ----------------
    state, theme, _ = _apply('{"op": "branch", "name": "main", "color": "#abcdef"}\n')

    # --- assert -----------------------
    main_id = state.branches["main"].id
    assert theme.branch_color_overrides[main_id] == "#abcdef"


def test_branch_op_without_color_writes_no_override() -> None:
    # --- arrange / act ----------------
    _, theme, _ = _apply('{"op": "branch", "name": "main"}\n')

    # --- assert -----------------------
    assert theme.branch_color_overrides == {}


def test_override_keyed_by_id_distinguishes_removed_and_redeclared_branch() -> None:
    """A removed branch and a fresh branch with the same name get different ids;
    only the live branch's override survives in the resolved theme."""
    # --- arrange / act ----------------
    state, theme, _ = _apply(
        '{"op": "branch", "name": "main"}\n'
        '{"op": "commit", "branch": "main", "id": "m1", "msg": "x"}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "color": "#111111"}\n'
        '{"op": "remove", "branches": ["feat"]}\n'
        '{"op": "branch", "name": "feat", "from_branch": "main", "color": "#222222"}\n'
    )

    # --- assert -----------------------
    # Only the live `feat` is in state.branches; its id maps to "#222222".
    live_feat = state.branches["feat"]
    assert theme.branch_color_overrides[live_feat.id] == "#222222"
    # No stale entry pointing at "#111111" survives.
    assert "#111111" not in theme.branch_color_overrides.values()
